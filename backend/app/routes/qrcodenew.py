# from fastapi import APIRouter, HTTPException, status, Request
# from fastapi.responses import JSONResponse
# from app.dependencies import user_dependency, db_dependency
# from app.services.qrcode import generate_qrcode
# from app.routes.auth import authenticate_user
# from app.services.security import create_access_token, decode_token
# from datetime import timedelta
# from app.crud.plans import get_plan_by_id
# from fastapi.responses import StreamingResponse

# router = APIRouter(
#     prefix="/qrcodenew",
#     tags=["qrcodenew"],
# )

# @router.get("/qr/{plan_id}")
# async def generate_specific_qrcode(
#     user: user_dependency, plan_id: int
# ):
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not authenticated",
#         )

#     # Create a unique, time-limited access token for this specific QR code
#     qr_access_token = create_access_token(
#         data={
#             "sub": str(user.get("user_id")),
#             "plan_id": plan_id,
#             "type": "qr_single_access"
#         },
#         expires_delta=timedelta(minutes=15)  # Short-lived token
#     )
#     print(f"access_token: {qr_access_token}")
#     # Construct the QR code URL with the token
#     verification_url = f"http://127.0.0.1:8000/qrcodenew/view?token={qr_access_token}"

#     # Generate QR code with the verification URL
#     qr_image = await generate_qrcode(data=verification_url)

#     return StreamingResponse(
#         qr_image,
#         media_type="image/png",
#         headers={"Content-Disposition": "attachment; filename=qrcode.png"},
#     )

# @router.get("/view")
# async def view_plan_via_qr(
#     token: str,
#     db: db_dependency
# ):
#     try:
#         # Decode and verify the token
#         payload = decode_token(token)

#         # Validate token type and contents
#         if payload.get('type') != 'qr_single_access':
#             raise HTTPException(status_code=401, detail="Invalid token")

#         # Extract plan_id from the token payload
#         plan_id = payload.get('plan_id')

#         # Validate plan_id is present
#         if not plan_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="No plan ID found in token"
#             )

#         # Fetch the plan using the new function
#         plan = await get_plan_by_id(db, plan_id)

#         return JSONResponse(
#             status_code=200,
#             content={
#                 "plan_id": plan.id,
#                 "plan_details": {
#                     "name": plan.name,
#                     "description": plan.description,
#                     "motivations": plan.motivations_data,
#                 }
#             }
#         )

#     except HTTPException as e:
#         # Error handling
#         return JSONResponse(
#             status_code=e.status_code,
#             content={
#                 "error": "Access Expired or Invalid",
#                 "message": str(e.detail)
#             }
#         )


















# @router.post("/verify-plan-access")
# async def verify_plan_access(
#     plan_id: int,
#     password: str,
#     db: db_dependency
# ):
#     """
#     Verify the plan-specific password and user ownership
#     """
#     # Check if the plan exists
#     plan = await get_plan_by_id(db, plan_id)
#     if not plan:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Plan not found"
#         )
#     # get user_id
#     user_id = await get_user_id_by_plan_id(plan_id, db)

#     # get user
#     hashed_password = await get_user_by_id(user_id, db)

#     # verify password
#     if not await verify_password(password, hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid access credentials"
#         )
#     # generate access token
#     access_token = await create_access_token(
#         data={
#             "plan_id": plan_id,
#             "user_id": user_id,
#             "type": "permanent_qr_access"
#         },
#         expires_delta=timedelta(minutes=15)  # Short-lived access
#     )


#     # Fetch plan details with motivations
#     plan_details = await get_plan_by_id(db, plan_id)

#     return {
#         "access_token": access_token,
#         "plan_id": plan_id,
#         "plan_details": {
#             "name": plan_details.name,
#             "description": plan_details.description,
#             "motivations": [
#                 {
#                     "id": motivation.id,
#                     "quote": motivation.quote,
#                     "link": motivation.link
#                 }
#                 for motivation in plan_details.motivation
#             ]
#         }
#     }




# @router.get("/view-permanent")
# async def view_permanent_plan(
#     plan_id: int,
#     db: db_dependency
# ):
#     """
#     Verify plan exists and prepare for password verification
#     """
#     # Verify the plan exists
#     plan = await get_plan_by_id(db, plan_id)

#     # Return a response that guides the frontend to show a password input
#     return JSONResponse(
#         status_code=200,
#         content={
#             "requires_password": True,
#             "plan_id": plan_id,
#             "plan_name": plan.name  # Optional: include plan name for UX
#         }
#     )
