# chat.py - Auto-generated
"""
Chat API endpoints for the Ready-To-Go application
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import asyncio

from config import settings
from models import get_db
from models.chat import ChatRequest, ChatResponse, MessageCreate, MessageRead, ConversationCreate, StreamingChatResponse
from modules.rag.context_builder import ContextBuilder
from modules.llm.interface import LLMInterface
from modules.vector_db.db import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
vector_store = VectorStore()
context_builder = ContextBuilder(vector_store)

# 대화 ID로 대화를 조회하는 함수
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get conversation by ID or raise 404"""
    from sqlalchemy import select
    from models.chat import Conversation
    
    statement = select(Conversation).where(Conversation.id == conversation_id)
    result = db.execute(statement).scalar_one_or_none()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    return result

# 새 대화 생성
@router.post("/conversation", response_model=Dict[str, Any])
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    from models.chat import Conversation
    
    conversation = Conversation(
        title=data.title,
        session_id=data.session_id,
        country_id=data.country_id,
        topic_id=data.topic_id,
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "session_id": conversation.session_id,
        "created_at": conversation.created_at
    }

# 단일 메시지 처리 → LLM 응답 생성 후 저장
@router.post("/message", response_model=ChatResponse)
async def process_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Process a chat message and return a response"""
    # Get or create conversation
    from models.chat import Conversation, Message
    
    conversation = None
    if request.conversation_id:
        conversation = await get_conversation(request.conversation_id, db)
    else:
        # Create new conversation
        conversation = Conversation(
            session_id=request.session_id,
            title=f"Conversation {uuid.uuid4().hex[:8]}"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Set country and topic if provided
    country = request.country
    topic = request.topic
    
    # Update conversation if country or topic was determined
    if (country or topic) and not request.conversation_id:
        if country:
            # Get country ID
            from sqlalchemy import select
            from models.metadata import Country
            stmt = select(Country).where(Country.name == country)
            country_obj = db.execute(stmt).scalar_one_or_none()
            if country_obj:
                conversation.country_id = country_obj.id
        
        if topic:
            # Get topic ID
            from sqlalchemy import select
            from models.metadata import Topic
            stmt = select(Topic).where(Topic.name == topic)
            topic_obj = db.execute(stmt).scalar_one_or_none()
            if topic_obj:
                conversation.topic_id = topic_obj.id
        
        db.commit()
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Build context using RAG
    context, references = context_builder.build_context(
        query=request.message,
        country=country,
        topic=topic,
        max_tokens=settings.MAX_CONTEXT_TOKENS
    )
    
    # Generate response
    llm = LLMInterface(model_name=request.model)
    response_text = await llm.generate_response(
        query=request.message,
        context=context,
        references=references,
        country=country,
        topic=topic,
        stream=False
    )
    
    # Save assistant message
    refs_json = [
        {
            "document_id": ref.get("document_id"),
            "title": ref.get("title"),
            "source": ref.get("source"),
            "url": ref.get("url")
        }
        for ref in references
    ]
    
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        source_references=refs_json
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    # Create response
    response = ChatResponse(
        message=MessageRead(
            id=assistant_message.id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at
        ),
        conversation_id=conversation.id,
        references=refs_json
    )
    
    return response

# 스트리밍 메시지 처리 → SSE로 LLM 응답을 순차 전송
@router.post("/message/stream")
async def stream_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Stream a chat response"""
    if not request.stream:
        raise HTTPException(status_code=400, detail="Stream parameter must be set to true")
    
    # Get or create conversation (same as in process_message)
    from models.chat import Conversation, Message
    
    conversation = None
    if request.conversation_id:
        conversation = await get_conversation(request.conversation_id, db)
    else:
        # Create new conversation
        conversation = Conversation(
            session_id=request.session_id,
            title=f"Conversation {uuid.uuid4().hex[:8]}"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Set country and topic if provided
    country = request.country
    topic = request.topic
    
    # Update conversation if country or topic was determined (same as in process_message)
    if (country or topic) and not request.conversation_id:
        if country:
            # Get country ID
            from sqlalchemy import select
            from models.metadata import Country
            stmt = select(Country).where(Country.name == country)
            country_obj = db.execute(stmt).scalar_one_or_none()
            if country_obj:
                conversation.country_id = country_obj.id
        
        if topic:
            # Get topic ID
            from sqlalchemy import select
            from models.metadata import Topic
            stmt = select(Topic).where(Topic.name == topic)
            topic_obj = db.execute(stmt).scalar_one_or_none()
            if topic_obj:
                conversation.topic_id = topic_obj.id
        
        db.commit()
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Build context using RAG
    context, references = context_builder.build_context(
        query=request.message,
        country=country,
        topic=topic,
        max_tokens=settings.MAX_CONTEXT_TOKENS
    )
    
    # Function to generate streaming response
    async def generate():
        response_chunks = []
        
        # Initialize LLM
        llm = LLMInterface(model_name=request.model)
        
        # Stream response
        async for chunk in llm.generate_response(
            query=request.message,
            context=context,
            references=references,
            country=country,
            topic=topic,
            stream=True
        ):
            # Store chunks for saving later
            response_chunks.append(chunk["content"])
            
            # Create streaming response
            if chunk["type"] == "token":
                data = StreamingChatResponse(
                    type="token",
                    content=chunk["content"],
                    references=None
                )
            elif chunk["type"] == "end":
                # Add references at the end
                refs_json = [
                    {
                        "document_id": ref.get("document_id"),
                        "title": ref.get("title"),
                        "source": ref.get("source"),
                        "url": ref.get("url")
                    }
                    for ref in references
                ]
                
                data = StreamingChatResponse(
                    type="end",
                    content="",
                    references=refs_json
                )
            else:
                continue
            
            # Yield data as server-sent event
            yield f"data: {json.dumps(data.dict())}\n\n"
        
        # Save assistant message after streaming is complete
        full_response = "".join(response_chunks)
        
        refs_json = [
            {
                "document_id": ref.get("document_id"),
                "title": ref.get("title"),
                "source": ref.get("source"),
                "url": ref.get("url")
            }
            for ref in references
        ]
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
            source_references=refs_json
        )
        
        # Use a new DB session for this operation
        from models import SessionLocal
        async_db = SessionLocal()
        try:
            async_db.add(assistant_message)
            async_db.commit()
        finally:
            async_db.close()
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

# 대화 ID로 대화의 메시지 히스토리 조회
@router.get("/history/{conversation_id}", response_model=List[MessageRead])
async def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get message history for a conversation"""
    conversation = await get_conversation(conversation_id, db)
    
    from sqlalchemy import select
    from models.chat import Message
    
    statement = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at)
    
    messages = db.execute(statement).scalars().all()
    
    return [
        MessageRead(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at
        )
        for message in messages
    ]

# 국가/토픽별 예시 질문 반환
@router.get("/examples", response_model=Dict[str, List[str]])
async def get_example_questions():
    """Get example questions for each country and topic"""
    examples = {
        "Australia-visa": [
            "호주 워킹홀리데이 비자 신청 방법은?",
            "What are the requirements for an Australian student visa?",
            "How long can I stay in Australia with a tourist visa?"
        ],
        "Australia-insurance": [
            "Do I need health insurance for Australia?",
            "호주 방문시 필요한 보험 종류",
            "What does travel insurance cover in Australia?"
        ],
        "Australia-immigration": [
            "호주 영주권 신청 절차",
            "What jobs are in demand for immigration to Australia?",
            "Australian permanent residency requirements"
        ],
        "Canada-visa": [
            "캐나다 학생비자 준비 서류",
            "How to apply for a Canadian work permit?",
            "What is the processing time for a Canadian visa?"
        ],
        "Canada-insurance": [
            "Is travel insurance mandatory for Canada?",
            "캐나다 방문시 의료보험 필수인가요?",
            "How much does health insurance cost in Canada?"
        ],
        "Canada-immigration": [
            "What is the Express Entry system in Canada?",
            "캐나다 이민 점수 계산 방법",
            "Requirements for Canadian citizenship"
        ],
        "France-visa": [
            "프랑스 학생비자 필요 서류",
            "How to get a long-stay visa for France?",
            "Schengen visa requirements for France"
        ],
        "France-insurance": [
            "Is health insurance required for France visa?",
            "프랑스 방문시 여행자 보험 추천",
            "What does French health insurance cover?"
        ],
        "France-immigration": [
            "How to get a residence permit in France?",
            "프랑스 영주권 취득 조건",
            "Working in France as a foreigner requirements"
        ]
    }
    
    return examples

# 사용 가능한 LLM 모델 목록 제공
@router.get("/settings/models", response_model=List[Dict[str, Any]])
async def get_available_models():
    """Get available LLM models for chat"""
    models = [
        {
            "id": "gpt-4",
            "name": "GPT-4",
            "provider": "OpenAI",
            "description": "Most capable GPT-4 model for complex tasks"
        },
        {
            "id": "gpt-3.5-turbo",
            "name": "GPT-3.5 Turbo",
            "provider": "OpenAI",
            "description": "Fast and efficient for most queries"
        },
        {
            "id": "gemini-pro",
            "name": "Gemini Pro",
            "provider": "Google",
            "description": "Google's most capable model for a wide range of tasks"
        },
        {
            "id": "gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "provider": "Google",
            "description": "Latest Gemini Pro model with enhanced capabilities"
        }
    ]
    
    # Add Claude models if API key is set
    # if settings.ANTHROPIC_API_KEY:
    #     models.extend([
    #         {
    #             "id": "claude-3-opus-20240229",
    #             "name": "Claude 3 Opus",
    #             "provider": "Anthropic",
    #             "description": "Most capable Claude model"
    #         },
    #         {
    #             "id": "claude-3-sonnet-20240229",
    #             "name": "Claude 3 Sonnet",
    #             "provider": "Anthropic",
    #             "description": "Balanced model for most tasks"
    #         }
    #     ])
    
    return models

# WebSocket 기반 채팅 인터페이스
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            request = ChatRequest(
                message=message_data.get("message"),
                conversation_id=message_data.get("conversation_id"),
                session_id=session_id,
                country=message_data.get("country"),
                topic=message_data.get("topic"),
                stream=True,
                model=message_data.get("model")
            )
            
            # Get or create conversation
            from models.chat import Conversation, Message
            
            conversation = None
            if request.conversation_id:
                try:
                    conversation = await get_conversation(request.conversation_id, db)
                except HTTPException:
                    # Send error message
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Conversation {request.conversation_id} not found"
                    })
                    continue
            else:
                # Create new conversation
                conversation = Conversation(
                    session_id=session_id,
                    title=f"Conversation {uuid.uuid4().hex[:8]}"
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                # Send conversation ID
                await websocket.send_json({
                    "type": "conversation_id",
                    "content": conversation.id
                })
            
            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=request.message
            )
            db.add(user_message)
            db.commit()
            
            # Set country and topic if provided
            country = request.country
            topic = request.topic
            
            # Build context
            context, references = context_builder.build_context(
                query=request.message,
                country=country,
                topic=topic,
                max_tokens=settings.MAX_CONTEXT_TOKENS
            )
            
            # Generate streaming response
            response_chunks = []
            
            # Initialize LLM
            llm = LLMInterface(model_name=request.model)
            
            # Stream response
            async for chunk in llm.generate_response(
                query=request.message,
                context=context,
                references=references,
                country=country,
                topic=topic,
                stream=True
            ):
                # Store chunks for saving later
                if chunk["type"] == "token":
                    response_chunks.append(chunk["content"])
                
                # Send chunk to client
                await websocket.send_json(chunk)
            
            # Save assistant message after streaming is complete
            full_response = "".join(response_chunks)
            
            refs_json = [
                {
                    "document_id": ref.get("document_id"),
                    "title": ref.get("title"),
                    "source": ref.get("source"),
                    "url": ref.get("url")
                }
                for ref in references
            ]
            
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
                source_references=refs_json
            )
            
            db.add(assistant_message)
            db.commit()
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Error: {str(e)}"
            })
        except:
            pass