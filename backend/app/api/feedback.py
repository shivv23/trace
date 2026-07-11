from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import FeedbackRequest
from app.models.db import (
    a_get_conversation, a_get_conversation_messages,
    a_update_message_feedback, a_log_feedback
)
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
async def submit_feedback(request: FeedbackRequest, user: dict = Depends(get_current_user)):
    conv = await a_get_conversation(request.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.get("user_id") and conv["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await a_get_conversation_messages(request.conversation_id)
    assistant_messages = [m for m in messages if m["role"] == "assistant"]

    if request.message_index >= len(assistant_messages):
        raise HTTPException(status_code=404, detail="Message not found")

    target = assistant_messages[request.message_index]
    prev_confidence = None
    conf = target.get("confidence")
    if conf and isinstance(conf, dict):
        prev_confidence = conf.get("overall")

    await a_update_message_feedback(
        target["id"],
        request.rating,
        request.corrected_answer,
    )

    await a_log_feedback(
        request.conversation_id,
        target["id"],
        request.rating,
        prev_confidence,
        user["id"],
    )

    return {"success": True, "message": "Feedback recorded"}
