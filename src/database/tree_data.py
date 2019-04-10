from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Declarative base for ORM-compatible class definitions. See SQLAlchemy documentation
Base = declarative_base()


class Setup:
    """Class containing all the SQLAlchemy DB connection necessities."""
    engine = create_engine("sqlite:///rtt_heatmap_data.db", echo=False)

    # Create a session for interacting with the database
    Session = sessionmaker(engine, autocommit=False)

    session = None

    @staticmethod
    def get_session():
        """
        Builds a new session and returns it.
        :return: Newly-generated session object.
        """
        return Setup.Session()


class TreeNode(Base):
    """
    An SQLAlchemy class representation of the nodes SQLite table. The table contains information about the number of
    success, failure, and running statuses of each node, alongside the node IDs and their parents' IDs.
    """

    __tablename__ = 'treenodes'

    id = Column(String, primary_key=True)
    tree_id = Column(String, primary_key=True)

    successes = Column(Integer)
    runnings = Column(Integer)
    failures = Column(Integer)
    waitings = Column(Integer)


Base.metadata.create_all(Setup.engine)

