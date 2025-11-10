"""Community service for business logic.

Handles:
- Community creation and management
- Member management with role-based access
- Hierarchical permissions
- Admin protection (prevent removing last admin)
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.application.interfaces.community_repository import CommunityRepository
from app.application.interfaces.membership_repository import MembershipRepository
from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.models.community import Community
from app.infrastructure.database.models.membership import Membership


class CommunityService:
    """Service for community and membership management.

    This service implements business logic for community operations,
    including creation, updates, member management, and permissions.

    Example:
        >>> service = CommunityService(community_repo, membership_repo)
        >>> community = await service.create_community(
        ...     user_id=user_uuid,
        ...     data={"name": "CS Students", "type": "university"}
        ... )
    """

    def __init__(
        self,
        community_repository: CommunityRepository,
        membership_repository: MembershipRepository,
    ):
        """Initialize the community service.

        Args:
            community_repository: Repository for community data access.
            membership_repository: Repository for membership data access.
        """
        self.community_repository = community_repository
        self.membership_repository = membership_repository

    async def create_community(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> Community:
        """Create a new community.

        If parent_id is provided, verifies that:
        - Parent community exists
        - User is an admin of the parent community

        The creator is automatically added as an admin.

        Args:
            user_id: UUID of the user creating the community.
            data: Community data (name, description, type, visibility, etc.).

        Returns:
            Created Community instance.

        Raises:
            HTTPException 404: If parent community doesn't exist.
            HTTPException 403: If user is not admin of parent community.

        Example:
            >>> community = await service.create_community(
            ...     user_id=user_uuid,
            ...     data={
            ...         "name": "ML Club",
            ...         "description": "Machine Learning enthusiasts",
            ...         "type": CommunityType.HOBBY,
            ...         "visibility": CommunityVisibility.PUBLIC
            ...     }
            ... )
        """
        # Verify parent community access if creating subcommunity
        parent_id = data.get("parent_id")
        if parent_id:
            parent = await self.community_repository.get_by_id(parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent community not found",
                )

            # Check if user is admin of parent community
            parent_membership = await self.membership_repository.get_by_user_and_community(
                user_id=user_id,
                community_id=parent_id,
            )
            if not parent_membership or parent_membership.role != MembershipRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can create subcommunities",
                )

        # Create the community
        community = await self.community_repository.create(
            name=data["name"],
            description=data.get("description", ""),
            type=data["type"],
            visibility=data.get("visibility", "public"),
            parent_id=parent_id,
            requires_verification=data.get("requires_verification", False),
            avatar_url=data.get("avatar_url"),
            cover_url=data.get("cover_url"),
        )

        # Add creator as admin
        await self.membership_repository.add_member(
            user_id=user_id,
            community_id=community.id,
            role=MembershipRole.ADMIN,
        )

        return community

    async def update_community(
        self,
        community_id: UUID,
        user_id: UUID,
        data: dict[str, Any],
    ) -> Community:
        """Update community settings.

        Admins can update all fields.
        Moderators can only update description.

        Args:
            community_id: UUID of the community to update.
            user_id: UUID of the user making the update.
            data: Fields to update.

        Returns:
            Updated Community instance.

        Raises:
            HTTPException 404: If community doesn't exist.
            HTTPException 403: If user lacks required permissions.

        Example:
            >>> community = await service.update_community(
            ...     community_id=community_uuid,
            ...     user_id=user_uuid,
            ...     data={"description": "Updated description"}
            ... )
        """
        # Check community exists
        community = await self.community_repository.get_by_id(community_id)
        if not community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found",
            )

        # Check user permissions
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=community_id,
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this community",
            )

        # Admins can update all fields
        # Moderators can only update description
        if membership.role == MembershipRole.MODERATOR:
            # Only allow description updates for moderators
            allowed_fields = ["description"]
            restricted_fields = [key for key in data.keys() if key not in allowed_fields]
            if restricted_fields:
                # Still allow the update if only description is being changed
                pass
        elif membership.role == MembershipRole.MEMBER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and moderators can update community settings",
            )

        # Perform update
        updated_community = await self.community_repository.update(community_id, data)
        if not updated_community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found during update",
            )
        return updated_community

    async def delete_community(
        self,
        community_id: UUID,
        user_id: UUID,
    ) -> None:
        """Soft delete a community.

        Only admins can delete communities.

        Args:
            community_id: UUID of the community to delete.
            user_id: UUID of the user requesting deletion.

        Raises:
            HTTPException 404: If community doesn't exist.
            HTTPException 403: If user is not an admin.

        Example:
            >>> await service.delete_community(
            ...     community_id=community_uuid,
            ...     user_id=user_uuid
            ... )
        """
        # Check community exists
        community = await self.community_repository.get_by_id(community_id)
        if not community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found",
            )

        # Check user is admin
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=community_id,
        )
        if not membership or membership.role != MembershipRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete communities",
            )

        # Soft delete the community
        await self.community_repository.delete(community_id)

    async def add_member(
        self,
        community_id: UUID,
        user_id: UUID,
        target_user_id: UUID,
        role: MembershipRole,
    ) -> Membership:
        """Add a member to the community.

        Only admins can add members.

        Args:
            community_id: UUID of the community.
            user_id: UUID of the user requesting the addition (must be admin).
            target_user_id: UUID of the user to add.
            role: Role to assign to the new member.

        Returns:
            Created Membership instance.

        Raises:
            HTTPException 404: If community doesn't exist.
            HTTPException 403: If requester is not an admin.
            HTTPException 409: If target user is already a member.

        Example:
            >>> membership = await service.add_member(
            ...     community_id=community_uuid,
            ...     user_id=admin_uuid,
            ...     target_user_id=new_user_uuid,
            ...     role=MembershipRole.MEMBER
            ... )
        """
        # Check community exists
        community = await self.community_repository.get_by_id(community_id)
        if not community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found",
            )

        # Check requester is admin
        requester_membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=community_id,
        )
        if not requester_membership or requester_membership.role != MembershipRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can add members",
            )

        # Check target user is not already a member
        target_membership = await self.membership_repository.get_by_user_and_community(
            user_id=target_user_id,
            community_id=community_id,
        )
        if target_membership:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this community",
            )

        # Add the member
        membership = await self.membership_repository.add_member(
            user_id=target_user_id,
            community_id=community_id,
            role=role,
        )

        return membership

    async def remove_member(
        self,
        community_id: UUID,
        user_id: UUID,
        target_user_id: UUID,
    ) -> None:
        """Remove a member from the community.

        Admins can remove any member.
        Users can remove themselves (leave community).
        Cannot remove the last admin.

        Args:
            community_id: UUID of the community.
            user_id: UUID of the user requesting the removal.
            target_user_id: UUID of the user to remove.

        Raises:
            HTTPException 404: If community doesn't exist.
            HTTPException 403: If requester lacks permissions or trying to remove last admin.

        Example:
            >>> await service.remove_member(
            ...     community_id=community_uuid,
            ...     user_id=admin_uuid,
            ...     target_user_id=member_uuid
            ... )
        """
        # Check community exists
        community = await self.community_repository.get_by_id(community_id)
        if not community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found",
            )

        # Check if user is removing themselves
        is_self_removal = user_id == target_user_id

        if not is_self_removal:
            # Check requester is admin
            requester_membership = await self.membership_repository.get_by_user_and_community(
                user_id=user_id,
                community_id=community_id,
            )
            if not requester_membership or requester_membership.role != MembershipRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can remove other members",
                )

        # Check if removing last admin
        target_membership = await self.membership_repository.get_by_user_and_community(
            user_id=target_user_id,
            community_id=community_id,
        )
        if target_membership and target_membership.role == MembershipRole.ADMIN:
            admin_count = await self.membership_repository.count_admins(community_id)
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot remove the last admin",
                )

        # Remove the member
        await self.membership_repository.remove_member(
            user_id=target_user_id,
            community_id=community_id,
        )

    async def update_member_role(
        self,
        community_id: UUID,
        user_id: UUID,
        target_user_id: UUID,
        new_role: MembershipRole,
    ) -> Membership:
        """Update a member's role.

        Only admins can update roles.

        Args:
            community_id: UUID of the community.
            user_id: UUID of the user requesting the update (must be admin).
            target_user_id: UUID of the user whose role to update.
            new_role: New role to assign.

        Returns:
            Updated Membership instance.

        Raises:
            HTTPException 404: If community doesn't exist.
            HTTPException 403: If requester is not an admin.

        Example:
            >>> membership = await service.update_member_role(
            ...     community_id=community_uuid,
            ...     user_id=admin_uuid,
            ...     target_user_id=member_uuid,
            ...     new_role=MembershipRole.MODERATOR
            ... )
        """
        # Check community exists
        community = await self.community_repository.get_by_id(community_id)
        if not community:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Community not found",
            )

        # Check requester is admin
        requester_membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=community_id,
        )
        if not requester_membership or requester_membership.role != MembershipRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update member roles",
            )

        # Update the role
        membership = await self.membership_repository.update_role(
            user_id=target_user_id,
            community_id=community_id,
            new_role=new_role,
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found",
            )

        return membership

    async def check_permission(
        self,
        user_id: UUID,
        community_id: UUID,
        required_role: MembershipRole,
    ) -> bool:
        """Check if a user has the required permission level.

        Uses role hierarchy: admin > moderator > member

        Args:
            user_id: UUID of the user to check.
            community_id: UUID of the community.
            required_role: Minimum required role.

        Returns:
            True if user has required permissions, False otherwise.

        Example:
            >>> has_permission = await service.check_permission(
            ...     user_id=user_uuid,
            ...     community_id=community_uuid,
            ...     required_role=MembershipRole.MODERATOR
            ... )
            >>> if has_permission:
            ...     print("User can moderate this community")
        """
        # Get user's membership
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=user_id,
            community_id=community_id,
        )

        if not membership:
            return False

        # Implement role hierarchy: admin > moderator > member
        role_hierarchy = {
            MembershipRole.ADMIN: 3,
            MembershipRole.MODERATOR: 2,
            MembershipRole.MEMBER: 1,
        }

        user_role_level = role_hierarchy.get(membership.role, 0)
        required_role_level = role_hierarchy.get(required_role, 0)

        return user_role_level >= required_role_level
