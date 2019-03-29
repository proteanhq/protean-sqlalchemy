"""Module to test Provider Class"""

from protean.conf import active_config

from protean_sqlalchemy.provider import SAProvider


class TestSAProvider:
    """Class to test Connection Handler class"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        cls.repo_conf = active_config.DATABASES['default']

    def test_init(self):
        """Test Initialization of Sqlalchemy DB"""
        provider = SAProvider(self.repo_conf)
        assert provider is not None

    def test_connection(self):
        """ Test the connection to the repository"""
        provider = SAProvider(self.repo_conf)
        conn = provider.get_connection()
        assert conn is not None

        # Execute a simple query to test the connection
        resp = conn.execute(
            'SELECT * FROM sqlite_master WHERE type="table"')
        assert list(resp) == []
