from models.documentshare import DocumentShare
from managers.user_manager import UserManager
from datetime import datetime

class DocumentManager:
    def __init__(self):
        self.session = UserManager().Session()

    def share_document(self, from_user_id, to_user_id, document_path, document_type):
        share = DocumentShare(
            shared_by_user_id=from_user_id,
            shared_to_user_id=to_user_id,
            document_path=document_path,
            document_type=document_type,
            shared_at=datetime.now(),
            status="active"
        )
        self.session.add(share)
        self.session.commit()
        return share

    def get_shares_for_user(self, user_id):
        return self.session.query(DocumentShare).filter_by(shared_to_user_id=user_id, status="active").all()

    def revoke_share(self, share_id):
        share = self.session.get(DocumentShare, share_id)
        if not share or share.status != "active":
            return False
        share.status = "revoked"
        self.session.commit()
        return True