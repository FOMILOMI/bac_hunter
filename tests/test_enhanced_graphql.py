"""
Unit tests for enhanced GraphQL testing functionality.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.plugins.enhanced_graphql import EnhancedGraphQLTester


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, status_code: int, json_data: Dict[str, Any] = None, 
                 headers: Dict[str, str] = None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {'content-type': 'application/json'}
        
    def json(self):
        return self._json_data


class TestEnhancedGraphQLTester:
    """Test the enhanced GraphQL tester functionality."""
    
    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        http = Mock()
        http.post = AsyncMock()
        return http
        
    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        db = Mock()
        db.add_finding_for_url = Mock()
        return db
        
    @pytest.fixture
    def graphql_tester(self, mock_http_client, mock_db):
        """Create a GraphQL tester instance."""
        tester = EnhancedGraphQLTester()
        tester.http = mock_http_client
        tester.db = mock_db
        return tester
        
    @pytest.mark.asyncio
    async def test_basic_graphql_detection_success(self, graphql_tester, mock_http_client):
        """Test successful GraphQL endpoint detection."""
        # Mock successful GraphQL response
        mock_response = MockResponse(200, {'data': {'__typename': 'Query'}})
        mock_http_client.post.return_value = mock_response
        
        result = await graphql_tester._test_basic_graphql("https://api.example.com/graphql")
        
        assert result['is_graphql'] is True
        assert 'detection_query' in result
        mock_http_client.post.assert_called()
        
    @pytest.mark.asyncio
    async def test_basic_graphql_detection_failure(self, graphql_tester, mock_http_client):
        """Test failed GraphQL endpoint detection."""
        # Mock non-GraphQL response
        mock_response = MockResponse(404, {})
        mock_http_client.post.return_value = mock_response
        
        result = await graphql_tester._test_basic_graphql("https://api.example.com/notgraphql")
        
        assert result['is_graphql'] is False
        
    @pytest.mark.asyncio
    async def test_introspection_enabled(self, graphql_tester, mock_http_client):
        """Test introspection detection when enabled."""
        # Mock introspection response
        introspection_data = {
            'data': {
                '__schema': {
                    'queryType': {'name': 'Query'},
                    'mutationType': {'name': 'Mutation'},
                    'types': [
                        {
                            'name': 'User',
                            'kind': 'OBJECT',
                            'fields': [
                                {'name': 'id', 'description': 'User ID'},
                                {'name': 'email', 'description': 'User email'}
                            ]
                        }
                    ]
                }
            }
        }
        
        mock_response = MockResponse(200, introspection_data)
        mock_http_client.post.return_value = mock_response
        
        result = await graphql_tester._test_introspection("https://api.example.com/graphql")
        
        assert result['enabled'] is True
        assert 'schema_info' in result
        assert len(result['schema_info']['types']) > 0
        
    @pytest.mark.asyncio
    async def test_introspection_disabled(self, graphql_tester, mock_http_client):
        """Test introspection detection when disabled."""
        # Mock disabled introspection response
        mock_response = MockResponse(400, {'errors': [{'message': 'Introspection disabled'}]})
        mock_http_client.post.return_value = mock_response
        
        result = await graphql_tester._test_introspection("https://api.example.com/graphql")
        
        assert result['enabled'] is False
        assert result['schema_info'] == {}
        
    def test_schema_analysis(self, graphql_tester):
        """Test GraphQL schema analysis."""
        schema_data = {
            'queryType': {'name': 'Query'},
            'mutationType': {'name': 'Mutation'},
            'types': [
                {
                    'name': 'Query',
                    'kind': 'OBJECT',
                    'fields': [
                        {'name': 'users', 'description': 'Get users'},
                        {'name': 'adminPanel', 'description': 'Admin panel access'}
                    ]
                },
                {
                    'name': 'User',
                    'kind': 'OBJECT',
                    'fields': [
                        {'name': 'id', 'description': 'User ID'},
                        {'name': 'email', 'description': 'User email', 'isDeprecated': True},
                        {'name': 'password', 'description': 'User password'},
                        {'name': 'adminRole', 'description': 'Admin role'}
                    ]
                }
            ]
        }
        
        analysis = graphql_tester._analyze_schema(schema_data)
        
        # Verify analysis results
        assert len(analysis['types']) == 2
        assert len(analysis['queries']) == 2
        assert len(analysis['sensitive_fields']) >= 1  # password field
        assert len(analysis['admin_fields']) >= 1    # adminPanel, adminRole
        
    def test_sensitive_field_detection(self, graphql_tester):
        """Test detection of sensitive fields."""
        sensitive_fields = [
            'password', 'secret_key', 'api_token', 'credit_card',
            'ssn', 'social_security', 'email', 'phone_number'
        ]
        
        for field in sensitive_fields:
            assert graphql_tester._is_sensitive_field(field)
            
        # Test case variations
        assert graphql_tester._is_sensitive_field('userPassword')
        assert graphql_tester._is_sensitive_field('SECRET_TOKEN')
        
        # Test non-sensitive fields
        non_sensitive = ['name', 'title', 'description', 'id']
        for field in non_sensitive:
            assert not graphql_tester._is_sensitive_field(field)
            
    def test_admin_field_detection(self, graphql_tester):
        """Test detection of admin fields."""
        admin_fields = [
            'admin', 'administrator', 'deleteUser', 'createUser',
            'manageUsers', 'systemSettings', 'internalData'
        ]
        
        for field in admin_fields:
            assert graphql_tester._is_admin_field(field)
            
        # Test case variations
        assert graphql_tester._is_admin_field('adminPanel')
        assert graphql_tester._is_admin_field('DELETE_USER')
        
        # Test non-admin fields
        non_admin = ['getUser', 'updateProfile', 'viewData']
        for field in non_admin:
            assert not graphql_tester._is_admin_field(field)
            
    @pytest.mark.asyncio
    async def test_authorization_bypass_detection(self, graphql_tester, mock_http_client):
        """Test authorization bypass vulnerability detection."""
        # Mock schema with sensitive fields
        schema_info = {
            'sensitive_fields': [
                {'type': 'User', 'field': 'password', 'description': 'User password'}
            ],
            'admin_fields': [
                {'type': 'Query', 'field': 'adminPanel', 'description': 'Admin panel'}
            ]
        }
        
        # Mock successful unauthorized access
        mock_response = MockResponse(200, {'data': {'password': 'secret123'}})
        mock_http_client.post.return_value = mock_response
        
        vulnerabilities = await graphql_tester._test_authorization_bypass(
            "https://api.example.com/graphql", 
            schema_info
        )
        
        assert len(vulnerabilities) > 0
        assert vulnerabilities[0]['type'] == 'authorization_bypass'
        assert vulnerabilities[0]['severity'] == 'high'
        
    @pytest.mark.asyncio
    async def test_query_complexity_testing(self, graphql_tester, mock_http_client):
        """Test query complexity and depth testing."""
        # Mock slow response to deep query
        async def mock_post_with_delay(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.1)  # Simulate slow response
            return MockResponse(200, {'data': {}})
            
        mock_http_client.post.side_effect = mock_post_with_delay
        
        with patch('time.time', side_effect=[0, 6]):  # 6 second response
            issues = await graphql_tester._test_query_complexity("https://api.example.com/graphql")
            
        assert len(issues) > 0
        assert issues[0]['type'] == 'query_complexity'
        assert issues[0]['response_time'] == 6.0
        
    def test_url_pattern_extraction(self, graphql_tester):
        """Test URL pattern extraction for grouping."""
        test_cases = [
            ("https://api.example.com/users/123", "https://api.example.com/users/ID"),
            ("https://api.example.com/docs/550e8400-e29b-41d4-a716-446655440000", 
             "https://api.example.com/docs/UUID"),
            ("https://api.example.com/search?q=test&page=1", 
             "https://api.example.com/search?PARAMS")
        ]
        
        for url, expected_pattern in test_cases:
            pattern = graphql_tester._extract_url_pattern(url)
            assert pattern == expected_pattern
            
    def test_url_similarity_calculation(self, graphql_tester):
        """Test URL similarity calculation."""
        # Similar URLs
        url1 = "https://api.example.com/users/123"
        url2 = "https://api.example.com/users/456"
        similarity = graphql_tester._calculate_url_similarity(url1, url2)
        assert similarity > 0.8
        
        # Different URLs
        url3 = "https://api.example.com/posts/123"
        similarity = graphql_tester._calculate_url_similarity(url1, url3)
        assert similarity < 0.8
        
    def test_content_similarity_calculation(self, graphql_tester):
        """Test content similarity calculation."""
        content1 = "user id 123 email john@example.com name John Doe"
        content2 = "user id 456 email jane@example.com name Jane Smith"
        
        similarity = graphql_tester._calculate_content_similarity(content1, content2)
        assert 0.3 < similarity < 0.9  # Some similarity but not identical
        
        # Identical content
        similarity = graphql_tester._calculate_content_similarity(content1, content1)
        assert similarity == 1.0
        
        # Completely different content
        content3 = "completely different text without common words"
        similarity = graphql_tester._calculate_content_similarity(content1, content3)
        assert similarity < 0.3
        
    def test_user_data_analysis(self, graphql_tester):
        """Test analysis of user-specific data in responses."""
        resp_a = {
            'url': 'https://api.example.com/user/123',
            'body': '{"user_id": "123", "email": "john@example.com", "name": "John"}'
        }
        
        resp_b = {
            'url': 'https://api.example.com/user/456', 
            'body': '{"user_id": "456", "email": "jane@example.com", "name": "Jane"}'
        }
        
        analysis = graphql_tester._analyze_content_for_user_data(resp_a, resp_b)
        
        assert analysis['suggests_cross_access'] is True
        assert len(analysis['data_a']) > 0
        assert len(analysis['data_b']) > 0
        
    def test_deep_query_generation(self, graphql_tester):
        """Test generation of deep nested queries."""
        query = graphql_tester._generate_deep_query(5)
        
        # Should contain nested structure
        assert query.startswith("query DeepQuery {")
        assert query.endswith("}")
        assert query.count("{") == 6  # DeepQuery + 5 nested levels
        assert "node0" in query
        assert "node4" in query
        assert "__typename" in query
        
    def test_wide_query_generation(self, graphql_tester):
        """Test generation of wide queries with many fields."""
        query = graphql_tester._generate_wide_query(10)
        
        assert query.startswith("query WideQuery {")
        assert query.endswith("}")
        assert "field0" in query
        assert "field9" in query
        
    def test_sensitive_info_detection_in_errors(self, graphql_tester):
        """Test detection of sensitive information in error messages."""
        sensitive_errors = [
            "Error: /home/user/app/config.py not found",
            "Database connection failed: mysql://user:pass@localhost",
            "Stack trace: File '/var/www/app.py', line 123",
            "SQL error: SELECT * FROM users WHERE id = 1"
        ]
        
        for error in sensitive_errors:
            assert graphql_tester._contains_sensitive_info(error)
            
        # Non-sensitive errors
        safe_errors = [
            "Field 'unknownField' not found",
            "Invalid query syntax",
            "Access denied"
        ]
        
        for error in safe_errors:
            assert not graphql_tester._contains_sensitive_info(error)
            
    @pytest.mark.asyncio
    async def test_endpoint_discovery(self, graphql_tester):
        """Test GraphQL endpoint discovery."""
        base_url = "https://api.example.com"
        target_id = 1
        
        # Mock database response
        graphql_tester.db.conn.return_value.__enter__.return_value.execute.return_value = [
            ("https://api.example.com/api/graphql",)
        ]
        
        endpoints = await graphql_tester._discover_graphql_endpoints(base_url, target_id)
        
        # Should include both discovered and common paths
        assert len(endpoints) > 1
        assert "https://api.example.com/graphql" in endpoints
        assert "https://api.example.com/api/graphql" in endpoints
        
    @pytest.mark.asyncio
    async def test_comprehensive_endpoint_testing(self, graphql_tester, mock_http_client):
        """Test comprehensive testing of a GraphQL endpoint."""
        # Mock basic GraphQL detection
        basic_response = MockResponse(200, {'data': {'__typename': 'Query'}})
        
        # Mock introspection response
        introspection_response = MockResponse(200, {
            'data': {
                '__schema': {
                    'queryType': {'name': 'Query'},
                    'types': [
                        {
                            'name': 'Query',
                            'kind': 'OBJECT',
                            'fields': [{'name': 'users'}]
                        }
                    ]
                }
            }
        })
        
        # Set up mock responses in order
        mock_http_client.post.side_effect = [
            basic_response,      # Basic detection
            introspection_response,  # Introspection
            MockResponse(200, {'data': {}}),  # Auth bypass test
            MockResponse(200, {'data': {}}),  # Complexity test
            MockResponse(200, {'data': {}}),  # Field access test
            MockResponse(200, {'data': {}}),  # Mutation test
            MockResponse(200, [{'data': {}}]),  # Batch test
            MockResponse(200, {'errors': [{'message': 'Field not found'}]})  # Error test
        ]
        
        results = await graphql_tester._test_graphql_endpoint("https://api.example.com/graphql", 1)
        
        assert results['is_graphql'] is True
        assert results['introspection_enabled'] is True
        assert 'vulnerabilities' in results
        assert 'security_issues' in results
        assert 'performance_issues' in results
        
    @pytest.mark.asyncio
    async def test_finding_storage(self, graphql_tester, mock_db):
        """Test storage of GraphQL findings."""
        results = {
            'is_graphql': True,
            'introspection_enabled': True,
            'schema_info': {
                'types': [{'name': 'User'}],
                'queries': ['users'],
                'mutations': ['createUser'],
                'sensitive_fields': [{'field': 'password'}]
            },
            'vulnerabilities': [
                {
                    'type': 'authorization_bypass',
                    'severity': 'high',
                    'description': 'Test vulnerability'
                }
            ],
            'security_issues': [],
            'performance_issues': []
        }
        
        await graphql_tester._store_enhanced_findings(1, "https://api.example.com/graphql", results)
        
        # Verify database calls
        assert mock_db.add_finding_for_url.called
        call_args_list = mock_db.add_finding_for_url.call_args_list
        
        # Should have stored multiple findings
        assert len(call_args_list) >= 2  # At least endpoint detection and introspection
        
    def test_id_pattern_analysis(self, graphql_tester):
        """Test analysis of ID patterns for predictability."""
        # Create mock responses with sequential IDs
        responses = [
            {'url': 'https://api.example.com/users/1', 'body': '{"id": 1}'},
            {'url': 'https://api.example.com/users/2', 'body': '{"id": 2}'},
            {'url': 'https://api.example.com/users/3', 'body': '{"id": 3}'},
            {'url': 'https://api.example.com/users/4', 'body': '{"id": 4}'},
            {'url': 'https://api.example.com/users/5', 'body': '{"id": 5}'}
        ]
        
        findings = graphql_tester._analyze_id_patterns(responses)
        
        assert len(findings) > 0
        assert findings[0]['type'] == 'IDOR'
        assert 'sequential' in findings[0]['title'].lower()
        
    @pytest.mark.asyncio
    async def test_offline_mode_handling(self, graphql_tester):
        """Test handling of offline mode."""
        with patch.dict(os.environ, {'BH_OFFLINE': '1'}):
            result = await graphql_tester.run("https://api.example.com", 1)
            
        # Should return empty list in offline mode
        assert result == []
        
    @pytest.mark.asyncio
    async def test_low_timeout_handling(self, graphql_tester):
        """Test handling of very low timeout settings."""
        # Mock low timeout setting
        mock_timeout_obj = Mock()
        mock_timeout_obj.timeout_seconds = 1.0
        graphql_tester.http = Mock()
        graphql_tester.http.s = mock_timeout_obj
        
        result = await graphql_tester.run("https://api.example.com", 1)
        
        # Should return empty list with very low timeout
        assert result == []