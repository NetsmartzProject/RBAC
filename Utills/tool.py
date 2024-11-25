from datetime import datetime , timedelta
from fastapi import Depends, status, HTTPException, Request
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from database import model,database
from uuid import UUID
from config.pydantic_config import settings
from database.database import get_db
from sqlalchemy import text, select,update
from sqlalchemy.orm import Session
from typing import Literal, List
from Schema.tool_schema import Tool,ToolResponse
from database.model import ToolMaster
from database.model import Organisation, ToolMaster,SubOrganisation,User

async def add_tool(tool: Tool, db: AsyncSession) -> ToolResponse:
    try:
        # Check if a tool with the same name already exists
        result = await db.execute(select(ToolMaster).filter(ToolMaster.tool_name == tool.toolname))
        existing_tool = result.scalar_one_or_none()  # Get the first result or None

        if existing_tool:
            # If tool already exists, raise an HTTP exception with status code 400
            raise HTTPException(status_code=400, detail="Tool with this name already exists.")
        
        # Create a new tool
        new_tool = ToolMaster(
            tool_name=tool.toolname,
            description=tool.description,
            is_active=True
        )
        print(new_tool, "this is my new Tool")
        
        # Add and commit the new tool to the database
        db.add(new_tool)
        await db.commit()
        await db.refresh(new_tool)
        
        # Return the response with the new tool details
        return ToolResponse(
            tool_id=new_tool.tool_id,
            tool_name=new_tool.tool_name,
            description=new_tool.description
        )

    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create tool: {str(e)}")
 
async def fetch_all_tools(db: AsyncSession) -> List[ToolResponse]:
    try:
        query = select(ToolMaster).where(ToolMaster.is_active == True)
        result = await db.execute(query)
        tools = result.scalars().all()
 
        return [
            ToolResponse(
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                description=tool.description
            )
            for tool in tools
        ]
 
    except Exception as e:
        print(f"Error fetching tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tools: {str(e)}")
 
async def fetch_tool_by_id(tool_id: UUID, db: AsyncSession) -> ToolResponse:
    try:
        query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
 
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found.")
 
        return ToolResponse(
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            description=tool.description
        )
 
    except Exception as e:
        print(f"Error fetching tool by ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tool: {str(e)}")

async def fetch_tool_by_name(tool_name: str, db: AsyncSession) -> ToolResponse:
    try:
        query = select(ToolMaster).where(ToolMaster.tool_name == tool_name, ToolMaster.is_active == True)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
 
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found.")
 
        return ToolResponse(
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            description=tool.description
        )
 
    except Exception as e:
        print(f"Error fetching tool by ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tool: {str(e)}")
 
async def update_tool(tool_id: UUID, tool_update: Tool, db: AsyncSession) -> ToolResponse:
    try:
        query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
 
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found.")
 
        tool.tool_name = tool_update.toolname
        tool.description = tool_update.description
 
        await db.commit()
        await db.refresh(tool)
 
        return ToolResponse(
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            description=tool.description
        )
 
    except Exception as e:
        await db.rollback()
        print(f"Error updating tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")
 
async def delete_tool(tool_id: UUID, db: AsyncSession):
    try:
        query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
 
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found.")
 
        tool.is_active = False  # Perform a soft delete
        await db.commit()
 
        return {"message": f"Tool with ID {tool_id} has been deactivated successfully."}
 
    except Exception as e:
        await db.rollback()
        print(f"Error deleting tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")

async def assign_tools_to_suborganisation(
    sub_org_id: UUID,
    tool_ids: list[UUID],
    db: AsyncSession
) -> dict:
    tool_query = await db.execute(select(ToolMaster).filter(ToolMaster.tool_id.in_(tool_ids)))
    existing_tools = tool_query.scalars().all()
    
    if len(existing_tools) != len(tool_ids):
        raise HTTPException(status_code=404, detail="One or more tools not found")

    org_query = await db.execute(select(SubOrganisation).filter(SubOrganisation.sub_org_id == sub_org_id))
    target_org = org_query.scalar()
    
    if not target_org:
        raise HTTPException(status_code=404, detail="Sub-organisation not found")

    parent_org = await db.execute(select(Organisation).filter(Organisation.org_id == target_org.org_id))
    parent_org = parent_org.scalar()
    
    if not parent_org:
        raise HTTPException(status_code=404, detail="Parent organisation not found")

    parent_tool_ids = set(parent_org.tool_ids or [])

    invalid_tools = [tool_id for tool_id in tool_ids if tool_id not in parent_tool_ids]
    
    if invalid_tools:
        raise HTTPException(status_code=400, detail=f"Tools {invalid_tools} are not available in the parent organisation")

    existing_tool_ids = set(target_org.tool_ids or [])
    new_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in existing_tool_ids]
    
    if not new_tool_ids:
        return {
            "message": "All provided tool IDs are already assigned to this sub-organisation",
            "sub_org_id": sub_org_id,
            "existing_tool_ids": list(existing_tool_ids)
        }

    updated_tool_ids = list(existing_tool_ids | set(new_tool_ids))
    updated_tool_grant_dates = (target_org.tool_grant_dates or []) + [datetime.now() for _ in new_tool_ids]
    
    target_org.tool_ids = updated_tool_ids
    target_org.tool_grant_dates = updated_tool_grant_dates

    print("Tool IDs before commit:", target_org.tool_ids)
    await db.commit()
    await db.refresh(target_org)
    print("Tool IDs after commit:", target_org.tool_ids)

    return {
        "message": "Tools assigned successfully",
        "sub_org_id": sub_org_id,
        "tool_ids": target_org.tool_ids
    }

# WORKING FINE FOR SUBORGANISATION ON THE BASIS OF ROLE

async def assign_tools_to_user(
    user_id: UUID,
    tool_ids: list[UUID],
    db: AsyncSession
) -> dict:
    tool_query = await db.execute(select(ToolMaster).filter(ToolMaster.tool_id.in_(tool_ids)))
    existing_tools = tool_query.scalars().all()
    
    if len(existing_tools) != len(tool_ids):
        raise HTTPException(status_code=404, detail="One or more tools not found")

    org_query = await db.execute(select(User).filter(User.user_id == user_id))
    target_org = org_query.scalar()
    
    if not target_org:
        raise HTTPException(status_code=404, detail="user not found")

    existing_tool_ids = set(target_org.tool_ids or [])
    new_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in existing_tool_ids]
    
    if not new_tool_ids:
        return {
            "message": "All provided tool IDs are already assigned to this user",
            "user_id": user_id,
            "existing_tool_ids": list(existing_tool_ids)
        }

    parent_org = await db.execute(select(SubOrganisation).filter(SubOrganisation.sub_org_id == target_org.sub_org_id))
    parent_org = parent_org.scalar()
    
    if not parent_org:
        raise HTTPException(status_code=404, detail="Parent organisation not found")

    parent_tool_ids = set(parent_org.tool_ids or [])

    invalid_tools = [tool_id for tool_id in tool_ids if tool_id not in parent_tool_ids]
    
    if invalid_tools:
        raise HTTPException(status_code=400, detail=f"Tools {invalid_tools} are not available in the parent sub-organisation")

    updated_tool_ids = list(existing_tool_ids | set(new_tool_ids))
    updated_tool_grant_dates = (target_org.tool_grant_dates or []) + [datetime.now() for _ in new_tool_ids]
    
    target_org.tool_ids = updated_tool_ids
    target_org.tool_grant_dates = updated_tool_grant_dates

    print("Tool IDs before commit:", target_org.tool_ids)
    await db.commit()
    await db.refresh(target_org)
    print("Tool IDs after commit:", target_org.tool_ids)

    return {
        "message": "Tools assigned successfully",
        "user_id": user_id,
        "tool_ids": target_org.tool_ids
    }

async def assign_tools_to_organisation(
    org_id: UUID,
    tool_ids: list[UUID],
    db: AsyncSession
) -> dict:
    # Fetch the tools that match the provided tool_ids
    tool_query = await db.execute(select(ToolMaster).filter(ToolMaster.tool_id.in_(tool_ids)))
    existing_tools = tool_query.scalars().all()
    
    # Check if all requested tools exist
    if len(existing_tools) != len(tool_ids):
        raise HTTPException(status_code=404, detail="One or more tools not found")

    # Fetch the organization (sub-organization) with the given org_id
    org_query = await db.execute(select(Organisation).filter(Organisation.org_id == org_id))
    target_org = org_query.scalar()
    
    # Check if the target organization exists
    if not target_org:
        raise HTTPException(status_code=404, detail="organisation not found")

    # Existing tool IDs in the target organization (handles the possibility of empty lists)
    existing_tool_ids = set(target_org.tool_ids or [])
    new_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in existing_tool_ids]
    
    # If no new tools to add, return a message and skip the update
    if not new_tool_ids:
        return {
            "message": "All provided tool IDs are already assigned to this organisation",
            "org_id": org_id,
            "existing_tool_ids": list(existing_tool_ids)
        }

    # Update the tool_ids and grant dates
    updated_tool_ids = list(existing_tool_ids | set(new_tool_ids))
    updated_tool_grant_dates = (target_org.tool_grant_dates or []) + [datetime.now() for _ in new_tool_ids]

    # Assign the new tool IDs and tool grant dates to the organization
    target_org.tool_ids = updated_tool_ids
    target_org.tool_grant_dates = updated_tool_grant_dates

    # Debugging: Output before and after commit for tool_ids
    print("Tool IDs before commit:", target_org.tool_ids)
    try:
        # Commit the changes to the database
        await db.commit()
        # Refresh to reflect the changes in the database
        await db.refresh(target_org)
        print("Tool IDs after commit:", target_org.tool_ids)
    except Exception as e:
        # If something goes wrong during commit, rollback changes
        await db.rollback()
        print(f"Error while committing changes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    # Return the success response
    return {
        "message": "Tools assigned successfully",
        "org_id": org_id,
        "tool_ids": target_org.tool_ids
    }

async def assign_hits_to_organisation(target_id: UUID, hits: int, db: AsyncSession):
    """Assign hits from SuperAdmin to an Organization."""
    # Fetch the organization and superadmin
    result = await db.execute(select(Organisation).filter(Organisation.org_id == target_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Ensure allocated_hits and available_hits are not None
    if organization.allocated_hits is None:
        organization.allocated_hits = 0
    if organization.available_hits is None:
        organization.available_hits = 0

    organization.allocated_hits = hits + organization.available_hits
    organization.available_hits = organization.allocated_hits

    await db.commit()
    return {"message": f"{hits} hits successfully assigned to Organization {target_id}"}


async def assign_hits_to_suborganisation(target_id: UUID, hits: int, db: AsyncSession):
    """Assign hits from Organization to a SubOrganization."""
    # Fetch the suborganization and its parent organization
    result = await db.execute(
        select(SubOrganisation).filter(SubOrganisation.sub_org_id == target_id))
    
    sub_org = result.scalar_one_or_none()
    org_id = sub_org.org_id
    org = await db.execute(select(Organisation).filter(Organisation.org_id == org_id))
    organization = org.scalar_one_or_none()

    if not sub_org:
        raise HTTPException(status_code=404, detail="SubOrganization not found")

    # Ensure available_hits in Organization is not None
    if organization.available_hits is None:
        organization.available_hits = 0

    # Check if Organization has enough hits
    if organization.available_hits < hits:
        raise HTTPException(status_code=400, detail="Insufficient hits available for Organization")

    # Ensure allocated_hits and available_hits in SubOrganization are not None
    if sub_org.allocated_hits is None:
        sub_org.allocated_hits = 0
    if sub_org.available_hits is None:
        sub_org.available_hits = 0

    # Deduct hits from Organization and assign to SubOrganization
    organization.available_hits -= hits
    sub_org.allocated_hits = hits + sub_org.available_hits
    sub_org.available_hits = sub_org.allocated_hits

    await db.commit()
    return {"message": f"{hits} hits successfully assigned to SubOrganization {target_id}"}


async def assign_hits_to_user(target_id: UUID, hits: int, db: AsyncSession):
    """Assign hits from SubOrganization to a User."""
    # Fetch the user and their parent SubOrganization
    result = await db.execute(
        select(User).filter(User.id == target_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sub_org_id = user.sub_org_id
    sub_org = await db.execute(select(SubOrganisation).filter(SubOrganisation.sub_org_id == sub_org_id))
    sub_organization = sub_org.scalar_one_or_none()

    # Ensure available_hits in User and SubOrganization are not None
    if user.available_hits is None:
        user.available_hits = 0
    if sub_organization.available_hits is None:
        sub_organization.available_hits = 0

    # Check if SubOrganization has enough hits
    if user.available_hits < hits:
        raise HTTPException(status_code=400, detail="Insufficient hits available for SubOrganization")

    # Deduct hits from SubOrganization and assign to User
    sub_organization.available_hits -= hits
    user.allocated_hits = hits + user.available_hits
    user.available_hits = user.allocated_hits

    await db.commit()
    return {"message": f"{hits} hits successfully assigned to User {target_id}"}

async def assign_ai_tokens_to_organisation(target_id: UUID, tokens: int, db: AsyncSession):
    """Assign AI tokens from SuperAdmin to an Organization."""
    # Fetch the organization and superadmin
    result = await db.execute(select(Organisation).filter(Organisation.org_id == target_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Ensure allocated_ai_tokens and remaining_ai_tokens are not None
    if organization.allocated_ai_tokens is None:
        organization.allocated_ai_tokens = 0
    if organization.remaining_ai_tokens is None:
        organization.remaining_ai_tokens = 0

    # Add tokens to the organization
    organization.allocated_ai_tokens = tokens + organization.remaining_ai_tokens
    organization.remaining_ai_tokens = organization.allocated_ai_tokens

    await db.commit()
    return {"message": f"{tokens} AI tokens successfully assigned to Organization {target_id}"}

async def assign_ai_tokens_to_suborganisation(target_id: UUID, tokens: int, db: AsyncSession):
    """Assign AI tokens from Organization to a SubOrganization."""
    # Fetch the suborganization and its parent organization
    result = await db.execute(
        select(SubOrganisation).filter(SubOrganisation.sub_org_id == target_id))
    
    sub_org = result.scalar_one_or_none()
    org_id = sub_org.org_id
    org = await db.execute(select(Organisation).filter(Organisation.org_id == org_id))
    organization = org.scalar_one_or_none()

    if not sub_org:
        raise HTTPException(status_code=404, detail="SubOrganization not found")

    # Ensure remaining_ai_tokens in Organization is not None
    if organization.remaining_ai_tokens is None:
        organization.remaining_ai_tokens = 0

    # Check if Organization has enough AI tokens
    if organization.remaining_ai_tokens < tokens:
        raise HTTPException(status_code=400, detail="Insufficient AI tokens available for Organization")

    # Ensure allocated_ai_tokens and remaining_ai_tokens in SubOrganization are not None
    if sub_org.allocated_ai_tokens is None:
        sub_org.allocated_ai_tokens = 0
    if sub_org.remaining_ai_tokens is None:
        sub_org.remaining_ai_tokens = 0

    # Deduct tokens from Organization and assign to SubOrganization
    organization.remaining_ai_tokens -= tokens
    sub_org.allocated_ai_tokens = tokens + sub_org.remaining_ai_tokens
    sub_org.remaining_ai_tokens = sub_org.allocated_ai_tokens

    await db.commit()
    return {"message": f"{tokens} AI tokens successfully assigned to SubOrganization {target_id}"}

async def assign_ai_tokens_to_user(target_id: UUID, tokens: int, db: AsyncSession):
    """Assign AI tokens from SubOrganization to a User."""
    # Fetch the user and their parent SubOrganization
    result = await db.execute(
        select(User).filter(User.id == target_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sub_org_id = user.sub_org_id
    sub_org = await db.execute(select(SubOrganisation).filter(SubOrganisation.sub_org_id == sub_org_id))
    sub_organization = sub_org.scalar_one_or_none()

    # Ensure remaining_ai_tokens in User and SubOrganization are not None
    if user.remaining_ai_tokens is None:
        user.remaining_ai_tokens = 0
    if sub_organization.remaining_ai_tokens is None:
        sub_organization.remaining_ai_tokens = 0

    # Check if SubOrganization has enough AI tokens
    if sub_organization.remaining_ai_tokens < tokens:
        raise HTTPException(status_code=400, detail="Insufficient AI tokens available for SubOrganization")

    # Deduct AI tokens from SubOrganization and assign to User
    sub_organization.remaining_ai_tokens -= tokens
    user.allocated_ai_tokens = tokens + user.remaining_ai_tokens
    user.remaining_ai_tokens = user.allocated_ai_tokens

    await db.commit()
    return {"message": f"{tokens} AI tokens successfully assigned to User {target_id}"}

async def fetch_available_hits(email:str, role: str, db: AsyncSession):
    if role == "user":
        result = await db.execute(
            select(User.available_hits).where(User.email == email)
        )
    elif role == "sub_org":
        result = await db.execute(
            select(SubOrganisation.available_hits).where(SubOrganisation.email == email)
        )
    elif role == "org":
        result = await db.execute(
            select(Organisation.available_hits).where(Organisation.email == email)
        )
    elif role == "superadmin":
        return {"Message": "There is no hit limit for superadmin"}
    else:
        return {"Message": "Please specify the correct role"}

    # Fetch scalar result (available_hits)
    available_hits = result.scalar()
    
    return {
        "available_hits":available_hits
    }

async def fetch_remaining_ai_tokens(email:str, role: str, db: AsyncSession):
    if role == "sub_org":
        result = await db.execute(
            select(SubOrganisation.remaining_ai_tokens).where(SubOrganisation.email == email)
        )
    elif role == "org":
        result = await db.execute(
            select(Organisation.remaining_ai_tokens).where(Organisation.email == email)
        )
    elif role == "user":
        result = await db.execute(
            select(User.available_hits).where(User.email == email)
        )
    elif role == "superadmin":
        return {"Message": "Superadmin does not have AI token restrictions"}
    else:
        return {"Message": "Invalid role specified"}

    # Fetch scalar result (remaining_ai_tokens)
    remaining_ai_tokens = result.scalar()
    
    return {
        "remaining_ai_tokens":remaining_ai_tokens
    }
