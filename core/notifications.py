import streamlit as st
from models.database import get_db, Notification
from sqlalchemy.orm import Session

def create_notification(db: Session, user_id: int, message: str, process_note_id: int = None):
    notification = Notification(
        user_id=user_id,
        message=message,
        process_note_id=process_note_id,
        is_read=0
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_unread_notifications(db: Session, user_id: int):
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == 0
    ).order_by(Notification.created_at.desc()).all()

def mark_as_read(db: Session, notification_id: int):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.is_read = 1
        db.commit()

def render_notifications_sidebar():
    if "current_user_id" not in st.session_state:
        return
        
    db = next(get_db())
    user_id = st.session_state.current_user_id
    
    unread_notifications = get_unread_notifications(db, user_id)
    count = len(unread_notifications)
    
    # We use a container or expander in the sidebar
    with st.sidebar:
        st.markdown("---")
        if count > 0:
            with st.expander(f"🔔 Notifications ({count})", expanded=True):
                for notif in unread_notifications:
                    st.info(notif.message)
                    if st.button("Mark as Read", key=f"read_{notif.id}"):
                        mark_as_read(db, notif.id)
                        st.rerun()
        else:
            with st.expander("🔔 Notifications (0)", expanded=False):
                st.write("You have no new notifications.")
