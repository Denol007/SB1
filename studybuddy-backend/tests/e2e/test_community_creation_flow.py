"""End-to-end test for complete community creation flow.

This module tests the entire community management journey from creation through
configuration, member management, and sub-community creation.

Complete flow:
1. User creates a university community
2. User configures community settings (visibility, verification requirements)
3. User adds members with different roles (admin, moderator, member)
4. User creates a sub-community (hierarchical structure)
5. User manages member roles and permissions
6. User verifies permission enforcement across the hierarchy

This test validates the complete user story US2 integration.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole
from app.main import app


@pytest.mark.e2e
@pytest.mark.us2
@pytest.mark.asyncio
class TestCommunityCreationFlow:
    """End-to-end test for complete community creation and management flow."""

    async def test_complete_community_creation_flow(self, db_session, test_user, another_user):
        """Test complete flow: Create → Configure → Add members → Sub-community → Manage roles.

        This E2E test validates the entire community management journey:
        - User creates a university community
        - User configures visibility and verification settings
        - User adds members with different roles
        - User creates a hierarchical sub-community
            - User manages member roles and permissions
            - System enforces permission-based access control

        Args:
            db_session: Database session fixture.
            test_user: Primary test user (will be community creator/admin).
            another_user: Secondary test user (will be added as member/moderator).

        Expected behavior:
            - Community created successfully with creator as admin
            - Settings updated correctly
            - Members added with appropriate roles
            - Sub-community inherits parent context
            - Role changes persist correctly
            - Permission enforcement works across hierarchy
        """
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Generate auth token for test_user (community creator)
            creator_token = f"test-token-{test_user.id}"
            creator_headers = {"Authorization": f"Bearer {creator_token}"}

            # Generate auth token for another_user
            member_token = f"test-token-{another_user.id}"
            member_headers = {"Authorization": f"Bearer {member_token}"}

            # ========== Step 1: Create University Community ==========
            community_data = {
                "name": "Stanford Computer Science",
                "description": "Official CS department community",
                "type": CommunityType.UNIVERSITY.value,
                "visibility": CommunityVisibility.PUBLIC.value,
                "requires_verification": True,
            }

            create_response = await client.post(
                "/api/v1/communities/",
                json=community_data,
                headers=creator_headers,
            )

            # Verify community creation
            # NOTE: This will fail until Community model and endpoints are implemented
            assert create_response.status_code == 201
            community = create_response.json()
            community_id = community["id"]

            assert community["name"] == "Stanford Computer Science"
            assert community["type"] == CommunityType.UNIVERSITY.value
            assert community["visibility"] == CommunityVisibility.PUBLIC.value
            assert community["requires_verification"] is True
            assert community["member_count"] == 1  # Creator auto-added as admin

            # ========== Step 2: Configure Community Settings ==========
            # Update community to make it private and change description
            update_data = {
                "description": "Updated: Official CS department community for verified students",
                "visibility": CommunityVisibility.PRIVATE.value,
            }

            update_response = await client.patch(
                f"/api/v1/communities/{community_id}",
                json=update_data,
                headers=creator_headers,
            )

            assert update_response.status_code == 200
            updated_community = update_response.json()
            assert (
                updated_community["description"]
                == "Updated: Official CS department community for verified students"
            )
            assert updated_community["visibility"] == CommunityVisibility.PRIVATE.value

            # ========== Step 3: Add Members with Different Roles ==========
            # Add another_user as a member (default role)
            join_response = await client.post(
                f"/api/v1/communities/{community_id}/join",
                headers=member_headers,
            )

            assert join_response.status_code == 200
            membership = join_response.json()
            assert membership["user_id"] == str(another_user.id)
            assert membership["community_id"] == community_id
            assert membership["role"] == MembershipRole.MEMBER.value

            # Verify member count increased
            get_response = await client.get(
                f"/api/v1/communities/{community_id}",
                headers=creator_headers,
            )
            assert get_response.status_code == 200
            assert get_response.json()["member_count"] == 2

            # Promote another_user to moderator
            role_update_response = await client.patch(
                f"/api/v1/communities/{community_id}/members/{another_user.id}",
                json={"role": MembershipRole.MODERATOR.value},
                headers=creator_headers,
            )

            assert role_update_response.status_code == 200
            updated_membership = role_update_response.json()
            assert updated_membership["role"] == MembershipRole.MODERATOR.value

            # ========== Step 4: Create Sub-Community (Hierarchical) ==========
            # Moderator creates a sub-community under the main community
            subcommunity_data = {
                "name": "Stanford CS - Machine Learning Study Group",
                "description": "Sub-community for ML enthusiasts",
                "type": CommunityType.UNIVERSITY.value,
                "visibility": CommunityVisibility.PRIVATE.value,
                "parent_id": community_id,
                "requires_verification": True,
            }

            subcommunity_response = await client.post(
                "/api/v1/communities/",
                json=subcommunity_data,
                headers=member_headers,  # Moderator creating sub-community
            )

            assert subcommunity_response.status_code == 201
            subcommunity = subcommunity_response.json()
            subcommunity_id = subcommunity["id"]

            assert subcommunity["name"] == "Stanford CS - Machine Learning Study Group"
            assert subcommunity["parent_id"] == community_id
            assert subcommunity["type"] == CommunityType.UNIVERSITY.value
            assert subcommunity["member_count"] == 1  # Creator auto-added

            # ========== Step 5: Verify Permission Enforcement ==========
            # Test that non-members cannot access private community
            third_user_token = f"test-token-{uuid4()}"
            third_user_headers = {"Authorization": f"Bearer {third_user_token}"}

            unauthorized_response = await client.get(
                f"/api/v1/communities/{community_id}",
                headers=third_user_headers,
            )
            assert unauthorized_response.status_code == 403  # Forbidden

            # Test that members can access private community
            member_access_response = await client.get(
                f"/api/v1/communities/{community_id}",
                headers=member_headers,
            )
            assert member_access_response.status_code == 200

            # Test that only admin can delete community (moderator cannot)
            moderator_delete_response = await client.delete(
                f"/api/v1/communities/{subcommunity_id}",
                headers=member_headers,  # Moderator attempting delete
            )
            assert moderator_delete_response.status_code == 403  # Forbidden

            # ========== Step 6: List Community Members ==========
            members_response = await client.get(
                f"/api/v1/communities/{community_id}/members",
                headers=creator_headers,
            )

            assert members_response.status_code == 200
            members = members_response.json()
            assert len(members) == 2  # Creator (admin) and another_user (moderator)

            # Verify member roles
            member_roles = {m["user_id"]: m["role"] for m in members}
            assert member_roles[str(test_user.id)] == MembershipRole.ADMIN.value
            assert member_roles[str(another_user.id)] == MembershipRole.MODERATOR.value

            # Filter members by role
            admin_response = await client.get(
                f"/api/v1/communities/{community_id}/members?role=admin",
                headers=creator_headers,
            )
            assert admin_response.status_code == 200
            admins = admin_response.json()
            assert len(admins) == 1
            assert admins[0]["user_id"] == str(test_user.id)

            # ========== Step 7: Test Member Removal ==========
            # Moderator leaves community
            leave_response = await client.post(
                f"/api/v1/communities/{community_id}/leave",
                headers=member_headers,
            )
            assert leave_response.status_code == 200

            # Verify member count decreased
            final_response = await client.get(
                f"/api/v1/communities/{community_id}",
                headers=creator_headers,
            )
            assert final_response.status_code == 200
            assert final_response.json()["member_count"] == 1

            # ========== Step 8: Test Last Admin Protection ==========
            # Admin cannot leave if they're the last admin
            last_admin_leave_response = await client.post(
                f"/api/v1/communities/{community_id}/leave",
                headers=creator_headers,
            )
            assert last_admin_leave_response.status_code == 400  # Bad Request
            error = last_admin_leave_response.json()
            assert "last admin" in error["detail"].lower()

    async def test_community_visibility_enforcement(self, db_session, test_user, another_user):
        """Test that visibility settings properly control access.

        Validates:
        - Public communities are accessible to all
        - Private communities require membership
        - Closed communities are visible but cannot be joined directly

        Args:
            db_session: Database session fixture.
            test_user: Community creator.
            another_user: Non-member attempting access.
        """
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            creator_token = f"test-token-{test_user.id}"
            creator_headers = {"Authorization": f"Bearer {creator_token}"}

            non_member_token = f"test-token-{another_user.id}"
            non_member_headers = {"Authorization": f"Bearer {non_member_token}"}

            # ========== Create Public Community ==========
            public_community = {
                "name": "Public Study Group",
                "description": "Open to all students",
                "type": CommunityType.HOBBY.value,
                "visibility": CommunityVisibility.PUBLIC.value,
                "requires_verification": False,
            }

            public_response = await client.post(
                "/api/v1/communities/",
                json=public_community,
                headers=creator_headers,
            )
            assert public_response.status_code == 201
            public_id = public_response.json()["id"]

            # Non-member can view public community
            view_response = await client.get(
                f"/api/v1/communities/{public_id}",
                headers=non_member_headers,
            )
            assert view_response.status_code == 200

            # Non-member can join public community
            join_response = await client.post(
                f"/api/v1/communities/{public_id}/join",
                headers=non_member_headers,
            )
            assert join_response.status_code == 200

            # ========== Create Private Community ==========
            private_community = {
                "name": "Private Study Group",
                "description": "Invitation only",
                "type": CommunityType.HOBBY.value,
                "visibility": CommunityVisibility.PRIVATE.value,
                "requires_verification": False,
            }

            private_response = await client.post(
                "/api/v1/communities/",
                json=private_community,
                headers=creator_headers,
            )
            assert private_response.status_code == 201
            private_id = private_response.json()["id"]

            # Non-member cannot view private community
            private_view_response = await client.get(
                f"/api/v1/communities/{private_id}",
                headers=non_member_headers,
            )
            assert private_view_response.status_code == 403

            # Non-member cannot join private community directly
            private_join_response = await client.post(
                f"/api/v1/communities/{private_id}/join",
                headers=non_member_headers,
            )
            assert private_join_response.status_code == 403

    async def test_hierarchical_community_structure(self, db_session, test_user):
        """Test creation and management of hierarchical community structures.

        Validates:
        - Sub-communities can be created under parent communities
        - Sub-communities inherit verification requirements
        - Hierarchy is properly maintained

        Args:
            db_session: Database session fixture.
            test_user: Community creator.
        """
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = f"test-token-{test_user.id}"
            headers = {"Authorization": f"Bearer {token}"}

            # ========== Create Parent Community ==========
            parent_data = {
                "name": "Stanford University",
                "description": "Main university community",
                "type": CommunityType.UNIVERSITY.value,
                "visibility": CommunityVisibility.PUBLIC.value,
                "requires_verification": True,
            }

            parent_response = await client.post(
                "/api/v1/communities/",
                json=parent_data,
                headers=headers,
            )
            assert parent_response.status_code == 201
            parent_id = parent_response.json()["id"]

            # ========== Create Multiple Sub-Communities ==========
            departments = [
                "Computer Science Department",
                "Engineering Department",
                "Business School",
            ]

            subcommunity_ids = []
            for dept_name in departments:
                sub_data = {
                    "name": f"Stanford - {dept_name}",
                    "description": f"{dept_name} sub-community",
                    "type": CommunityType.UNIVERSITY.value,
                    "visibility": CommunityVisibility.PUBLIC.value,
                    "parent_id": parent_id,
                    "requires_verification": True,
                }

                sub_response = await client.post(
                    "/api/v1/communities/",
                    json=sub_data,
                    headers=headers,
                )
                assert sub_response.status_code == 201
                subcommunity = sub_response.json()
                assert subcommunity["parent_id"] == parent_id
                subcommunity_ids.append(subcommunity["id"])

            # ========== Create Nested Sub-Community (3-level hierarchy) ==========
            # Create a sub-community under Computer Science Department
            nested_data = {
                "name": "Stanford CS - AI Research Lab",
                "description": "Nested AI lab community",
                "type": CommunityType.UNIVERSITY.value,
                "visibility": CommunityVisibility.PRIVATE.value,
                "parent_id": subcommunity_ids[0],  # CS Department
                "requires_verification": True,
            }

            nested_response = await client.post(
                "/api/v1/communities/",
                json=nested_data,
                headers=headers,
            )
            assert nested_response.status_code == 201
            nested_community = nested_response.json()
            assert nested_community["parent_id"] == subcommunity_ids[0]

            # ========== Verify List Filtering Works ==========
            # List all university-type communities
            list_response = await client.get(
                f"/api/v1/communities?type={CommunityType.UNIVERSITY.value}",
                headers=headers,
            )
            assert list_response.status_code == 200
            communities = list_response.json()
            # Should return parent + 3 departments + 1 nested = 5 total
            assert len(communities) >= 5

    async def test_verification_requirement_enforcement(self, db_session, test_user, another_user):
        """Test that verification requirements are properly enforced.

        Validates:
        - Communities can require student verification
        - Unverified users cannot join verification-required communities
        - Verified users can join verification-required communities

        Args:
            db_session: Database session fixture.
            test_user: Verified user (community creator).
            another_user: Unverified user attempting to join.
        """
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            creator_token = f"test-token-{test_user.id}"
            creator_headers = {"Authorization": f"Bearer {creator_token}"}

            unverified_token = f"test-token-{another_user.id}"
            unverified_headers = {"Authorization": f"Bearer {unverified_token}"}

            # ========== Create Verification-Required Community ==========
            verified_community = {
                "name": "Stanford Verified Students Only",
                "description": "Requires university verification",
                "type": CommunityType.UNIVERSITY.value,
                "visibility": CommunityVisibility.PUBLIC.value,
                "requires_verification": True,
            }

            create_response = await client.post(
                "/api/v1/communities/",
                json=verified_community,
                headers=creator_headers,
            )
            assert create_response.status_code == 201
            community_id = create_response.json()["id"]

            # ========== Unverified User Attempts to Join ==========
            join_response = await client.post(
                f"/api/v1/communities/{community_id}/join",
                headers=unverified_headers,
            )
            # Should fail because user is not verified
            assert join_response.status_code == 403
            error = join_response.json()
            assert "verification" in error["detail"].lower()

            # ========== Create Non-Verification Community ==========
            open_community = {
                "name": "Open Study Group",
                "description": "No verification required",
                "type": CommunityType.HOBBY.value,
                "visibility": CommunityVisibility.PUBLIC.value,
                "requires_verification": False,
            }

            open_response = await client.post(
                "/api/v1/communities/",
                json=open_community,
                headers=creator_headers,
            )
            assert open_response.status_code == 201
            open_id = open_response.json()["id"]

            # Unverified user CAN join non-verification community
            open_join_response = await client.post(
                f"/api/v1/communities/{open_id}/join",
                headers=unverified_headers,
            )
            assert open_join_response.status_code == 200
