# relational_metadata_handler.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.models import Tenant, Dataset

class RelationalMetadataHandler:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = self.SessionLocal()

    def get_dataset_id(self, tenant_name, dataset_name):
        tenant = self.db_session.query(Tenant).filter_by(name=tenant_name).first()
        if not tenant:
            raise ValueError(f"No tenant found with name '{tenant_name}'")

        dataset = self.db_session.query(Dataset).filter_by(tenant_id=tenant.tenant_id, name=dataset_name).first()
        if not dataset:
            raise ValueError(f"No dataset found with name '{dataset_name}' for tenant '{tenant_name}'")

        return dataset.dataset_id
