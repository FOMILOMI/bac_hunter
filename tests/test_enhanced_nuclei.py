"""
Unit tests for enhanced Nuclei integration.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.integrations.enhanced_nuclei import EnhancedNucleiRunner


class TestEnhancedNucleiRunner:
    """Test the enhanced Nuclei integration functionality."""
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage object."""
        storage = Mock()
        storage.add_finding_for_url = Mock()
        return storage
        
    @pytest.fixture
    def mock_external_tool_runner(self):
        """Create a mock external tool runner."""
        runner = Mock()
        runner.run_tool = AsyncMock()
        return runner
        
    @pytest.fixture
    def nuclei_runner(self, mock_storage):
        """Create a Nuclei runner instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = EnhancedNucleiRunner(mock_storage)
            runner.custom_templates_dir = Path(temp_dir) / "templates"
            runner.custom_templates_dir.mkdir(exist_ok=True)
            yield runner
            
    @pytest.fixture
    def mock_nuclei_available(self):
        """Mock Nuclei being available in PATH."""
        with patch('shutil.which', return_value='/usr/bin/nuclei'):
            yield
            
    @pytest.mark.asyncio
    async def test_initialization_success(self, nuclei_runner, mock_nuclei_available):
        """Test successful initialization."""
        with patch.object(nuclei_runner, '_update_nuclei_templates', return_value=True):
            with patch.object(nuclei_runner, '_ensure_custom_templates'):
                result = await nuclei_runner.initialize()
                
        assert result is True
        
    @pytest.mark.asyncio
    async def test_initialization_nuclei_not_found(self, nuclei_runner):
        """Test initialization when Nuclei is not available."""
        with patch('shutil.which', return_value=None):
            result = await nuclei_runner.initialize()
            
        assert result is False
        
    @pytest.mark.asyncio
    async def test_update_nuclei_templates_success(self, nuclei_runner, mock_nuclei_available):
        """Test successful Nuclei template update."""
        nuclei_runner.runner.run_tool.return_value = {'success': True, 'stdout': ''}
        
        result = await nuclei_runner._update_nuclei_templates()
        
        assert result is True
        nuclei_runner.runner.run_tool.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_update_nuclei_templates_failure(self, nuclei_runner, mock_nuclei_available):
        """Test failed Nuclei template update."""
        nuclei_runner.runner.run_tool.return_value = {'success': False, 'error': 'Update failed'}
        
        result = await nuclei_runner._update_nuclei_templates()
        
        assert result is False
        
    @pytest.mark.asyncio
    async def test_custom_template_creation(self, nuclei_runner):
        """Test creation of custom BAC templates."""
        await nuclei_runner._ensure_custom_templates()
        
        # Check that template files were created
        template_files = list(nuclei_runner.custom_templates_dir.glob("*.yaml"))
        assert len(template_files) >= 5  # At least 5 custom templates
        
        # Check specific templates
        template_names = [f.stem for f in template_files]
        expected_templates = [
            'bac-hunter-idor',
            'bac-hunter-privilege-escalation', 
            'bac-hunter-auth-bypass',
            'bac-hunter-session-fixation',
            'bac-hunter-info-disclosure'
        ]
        
        for expected in expected_templates:
            assert expected in template_names
            
    def test_idor_template_creation(self, nuclei_runner):
        """Test IDOR template creation."""
        template_name, template_content = nuclei_runner._create_idor_template()
        
        assert template_name == 'bac-hunter-idor'
        assert template_content['id'] == 'bac-hunter-idor'
        assert template_content['info']['severity'] == 'high'
        assert 'idor' in template_content['info']['tags']
        assert len(template_content['requests']) > 0
        
    def test_privilege_escalation_template_creation(self, nuclei_runner):
        """Test privilege escalation template creation."""
        template_name, template_content = nuclei_runner._create_privilege_escalation_template()
        
        assert template_name == 'bac-hunter-privilege-escalation'
        assert template_content['info']['severity'] == 'critical'
        assert 'privilege-escalation' in template_content['info']['tags']
        
    def test_auth_bypass_template_creation(self, nuclei_runner):
        """Test authentication bypass template creation."""
        template_name, template_content = nuclei_runner._create_auth_bypass_template()
        
        assert template_name == 'bac-hunter-auth-bypass'
        assert template_content['info']['severity'] == 'high'
        assert 'auth-bypass' in template_content['info']['tags']
        
        # Check for IP headers
        request = template_content['requests'][0]
        headers = request['headers']
        assert 'X-Forwarded-For' in headers
        assert 'X-Real-IP' in headers
        
    def test_scan_config_building_basic(self, nuclei_runner):
        """Test building basic scan configuration."""
        config = nuclei_runner._build_scan_config(None, None)
        
        assert 'bac_focused' in config
        assert 'idor' in config['bac_focused']['tags']
        assert 'broken-access-control' in config['bac_focused']['tags']
        
    def test_scan_config_building_with_context(self, nuclei_runner):
        """Test building scan configuration with context."""
        context = {
            'application_type': 'api',
            'authentication_detected': True
        }
        
        config = nuclei_runner._build_scan_config(context, ['custom-tag'])
        
        assert 'bac_focused' in config
        assert 'api_focused' in config
        assert 'auth_focused' in config
        assert 'custom' in config
        
        assert 'api' in config['api_focused']['tags']
        assert 'auth-bypass' in config['auth_focused']['tags']
        assert 'custom-tag' in config['custom']['tags']
        
    @pytest.mark.asyncio
    async def test_run_nuclei_scan_success(self, nuclei_runner, mock_nuclei_available):
        """Test successful Nuclei scan execution."""
        # Mock successful scan result
        mock_finding = {
            'template-id': 'test-template',
            'matched-at': 'https://example.com/test',
            'info': {'severity': 'high', 'name': 'Test Finding'}
        }
        
        mock_stdout = json.dumps(mock_finding) + '\n'
        nuclei_runner.runner.run_tool.return_value = {
            'success': True,
            'stdout': mock_stdout
        }
        
        scan_params = {
            'tags': ['idor', 'broken-access-control'],
            'severity': ['critical', 'high']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("https://example.com\n")
            targets_file = f.name
            
        try:
            results = await nuclei_runner._run_nuclei_scan(targets_file, scan_params, 1.0, 'test_scan')
            
            assert len(results) == 1
            assert results[0]['template-id'] == 'test-template'
            assert results[0]['scan_name'] == 'test_scan'
            assert 'timestamp' in results[0]
            
        finally:
            Path(targets_file).unlink(missing_ok=True)
            
    @pytest.mark.asyncio
    async def test_run_nuclei_scan_failure(self, nuclei_runner, mock_nuclei_available):
        """Test failed Nuclei scan execution."""
        nuclei_runner.runner.run_tool.return_value = {
            'success': False,
            'error': 'Scan failed'
        }
        
        scan_params = {'tags': ['test']}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("https://example.com\n")
            targets_file = f.name
            
        try:
            results = await nuclei_runner._run_nuclei_scan(targets_file, scan_params, 1.0, 'test_scan')
            assert results == []
        finally:
            Path(targets_file).unlink(missing_ok=True)
            
    def test_bac_vulnerability_classification(self, nuclei_runner):
        """Test BAC vulnerability classification."""
        test_cases = [
            ({'template-id': 'test-idor-vuln'}, 'IDOR'),
            ({'template-id': 'privilege-escalation-test'}, 'Privilege Escalation'),
            ({'template-id': 'auth-bypass-test'}, 'Authentication Bypass'),
            ({'template-id': 'session-fixation-test'}, 'Session Management'),
            ({'template-id': 'info-disclosure-test'}, 'Information Disclosure'),
            ({'template-id': 'unknown-template'}, 'Access Control')
        ]
        
        for finding, expected_category in test_cases:
            category = nuclei_runner._classify_bac_vulnerability(finding)
            assert category == expected_category
            
    def test_risk_assessment_basic(self, nuclei_runner):
        """Test basic risk assessment."""
        finding = {
            'template-id': 'test-template',
            'info': {'severity': 'high'}
        }
        
        risk = nuclei_runner._assess_risk(finding, None)
        
        assert risk['base_severity'] == 'high'
        assert risk['final_severity'] in ['low', 'medium', 'high', 'critical']
        assert risk['risk_score'] >= 1
        assert isinstance(risk['risk_factors'], list)
        assert risk['risk_multiplier'] >= 1.0
        
    def test_risk_assessment_with_context(self, nuclei_runner):
        """Test risk assessment with context."""
        finding = {
            'template-id': 'admin-privilege-escalation',
            'info': {'severity': 'high'}
        }
        
        context = {
            'application_type': 'financial',
            'public_facing': True,
            'authentication_required': True
        }
        
        risk = nuclei_runner._assess_risk(finding, context)
        
        # Should have increased risk due to context
        assert risk['risk_multiplier'] > 1.0
        assert len(risk['risk_factors']) > 0
        assert 'High-value target application' in risk['risk_factors']
        assert 'Public-facing application' in risk['risk_factors']
        
    def test_remediation_suggestions(self, nuclei_runner):
        """Test remediation suggestion generation."""
        idor_finding = {'template-id': 'idor-test'}
        suggestions = nuclei_runner._get_remediation_suggestions(idor_finding)
        
        assert len(suggestions) > 0
        assert any('authorization' in s.lower() for s in suggestions)
        assert any('uuid' in s.lower() or 'identifier' in s.lower() for s in suggestions)
        
    def test_owasp_mapping(self, nuclei_runner):
        """Test OWASP category mapping."""
        findings = [
            ({'template-id': 'idor-test'}, 'A01:2021 - Broken Access Control'),
            ({'template-id': 'privilege-escalation'}, 'A01:2021 - Broken Access Control'),
            ({'template-id': 'auth-bypass'}, 'A07:2021 - Identification and Authentication Failures')
        ]
        
        for finding, expected_owasp in findings:
            mapping = nuclei_runner._map_to_owasp(finding)
            assert mapping['top10'] == expected_owasp
            assert 'category' in mapping
            assert 'cwe' in mapping
            
    def test_finding_enhancement(self, nuclei_runner):
        """Test finding enhancement with additional context."""
        original_finding = {
            'template-id': 'test-idor',
            'matched-at': 'https://example.com/api/users/123',
            'info': {'severity': 'high', 'name': 'IDOR Test'}
        }
        
        context = {'application_type': 'api'}
        
        enhanced = nuclei_runner._enhance_finding(original_finding, context)
        
        # Should have additional fields
        assert 'bac_category' in enhanced
        assert 'risk_assessment' in enhanced
        assert 'remediation' in enhanced
        assert 'owasp_mapping' in enhanced
        
        # Original fields should be preserved
        assert enhanced['template-id'] == 'test-idor'
        assert enhanced['matched-at'] == 'https://example.com/api/users/123'
        
    def test_finding_deduplication(self, nuclei_runner):
        """Test finding deduplication."""
        findings = [
            {'template-id': 'test-1', 'matched-at': 'https://example.com/test'},
            {'template-id': 'test-1', 'matched-at': 'https://example.com/test'},  # Duplicate
            {'template-id': 'test-2', 'matched-at': 'https://example.com/other'}
        ]
        
        processed = nuclei_runner._post_process_results(findings, None)
        
        # Should have deduplicated
        assert len(processed) == 2
        
        # Check unique findings
        finding_ids = [nuclei_runner._generate_finding_id(f) for f in processed]
        assert len(set(finding_ids)) == len(finding_ids)
        
    def test_finding_storage(self, nuclei_runner):
        """Test storage of enhanced findings."""
        finding = {
            'template-id': 'test-idor',
            'matched-at': 'https://example.com/api/users/123',
            'info': {'severity': 'high', 'name': 'IDOR Test'},
            'bac_category': 'IDOR',
            'risk_assessment': {
                'final_severity': 'high',
                'risk_score': 8.0
            }
        }
        
        nuclei_runner._store_nuclei_finding(finding)
        
        # Verify database call
        nuclei_runner.db.add_finding_for_url.assert_called_once()
        call_args = nuclei_runner.db.add_finding_for_url.call_args
        
        assert call_args[0][0] == 'https://example.com/api/users/123'  # URL
        assert 'nuclei_idor' in call_args[0][1]  # Finding type
        assert 'IDOR Test' in call_args[0][2]  # Description
        assert call_args[0][3] == 0.8  # Score for high severity
        
    @pytest.mark.asyncio
    async def test_comprehensive_scan_workflow(self, nuclei_runner, mock_nuclei_available):
        """Test complete scan workflow."""
        # Mock initialization
        with patch.object(nuclei_runner, '_update_nuclei_templates', return_value=True):
            with patch.object(nuclei_runner, '_ensure_custom_templates'):
                # Mock scan results
                mock_finding = {
                    'template-id': 'bac-hunter-idor',
                    'matched-at': 'https://example.com/api/users/123',
                    'info': {'severity': 'high', 'name': 'IDOR Vulnerability'}
                }
                
                mock_stdout = json.dumps(mock_finding) + '\n'
                nuclei_runner.runner.run_tool.return_value = {
                    'success': True,
                    'stdout': mock_stdout
                }
                
                targets = ['https://example.com']
                context = {'application_type': 'api'}
                
                results = await nuclei_runner.scan_with_context(targets, context, rps=1.0)
                
                assert len(results) > 0
                assert results[0]['template-id'] == 'bac-hunter-idor'
                assert 'bac_category' in results[0]
                assert 'risk_assessment' in results[0]
                
    @pytest.mark.asyncio
    async def test_report_generation(self, nuclei_runner):
        """Test comprehensive report generation."""
        findings = [
            {
                'template-id': 'test-idor',
                'bac_category': 'IDOR',
                'risk_assessment': {'final_severity': 'high'},
                'remediation': ['Fix IDOR vulnerability'],
                'owasp_mapping': {'top10': 'A01:2021 - Broken Access Control'}
            },
            {
                'template-id': 'test-auth',
                'bac_category': 'Authentication Bypass',
                'risk_assessment': {'final_severity': 'critical'},
                'remediation': ['Fix auth bypass'],
                'owasp_mapping': {'top10': 'A07:2021 - Identification and Authentication Failures'}
            }
        ]
        
        report = await nuclei_runner.generate_nuclei_report(findings)
        
        assert report['total_findings'] == 2
        assert 'high' in report['findings_by_severity']
        assert 'critical' in report['findings_by_severity']
        assert 'IDOR' in report['findings_by_category']
        assert len(report['top_recommendations']) > 0
        assert len(report['owasp_coverage']) > 0
        
    @pytest.mark.asyncio
    async def test_empty_report_generation(self, nuclei_runner):
        """Test report generation with no findings."""
        report = await nuclei_runner.generate_nuclei_report([])
        
        assert report['total_findings'] == 0
        assert report['findings_by_severity'] == {}
        assert report['findings_by_category'] == {}
        assert 'No Nuclei findings' in report['summary']
        
    def test_top_recommendations_generation(self, nuclei_runner):
        """Test generation of top recommendations."""
        findings = [
            {'remediation': ['Fix IDOR', 'Use proper auth']},
            {'remediation': ['Fix IDOR', 'Validate input']},
            {'remediation': ['Use proper auth', 'Add logging']}
        ]
        
        recommendations = nuclei_runner._generate_top_recommendations(findings)
        
        # Should return most common recommendations first
        assert len(recommendations) <= 5
        assert 'Fix IDOR' in recommendations  # Should be most common
        assert 'Use proper auth' in recommendations
        
    def test_owasp_coverage_calculation(self, nuclei_runner):
        """Test OWASP Top 10 coverage calculation."""
        findings = [
            {'owasp_mapping': {'top10': 'A01:2021 - Broken Access Control'}},
            {'owasp_mapping': {'top10': 'A01:2021 - Broken Access Control'}},
            {'owasp_mapping': {'top10': 'A07:2021 - Identification and Authentication Failures'}}
        ]
        
        coverage = nuclei_runner._calculate_owasp_coverage(findings)
        
        assert coverage['A01:2021 - Broken Access Control'] == 2
        assert coverage['A07:2021 - Identification and Authentication Failures'] == 1
        
    def test_finding_id_generation(self, nuclei_runner):
        """Test unique finding ID generation."""
        finding1 = {'template-id': 'test-1', 'matched-at': 'https://example.com/test'}
        finding2 = {'template-id': 'test-2', 'matched-at': 'https://example.com/test'}
        finding3 = {'template-id': 'test-1', 'matched-at': 'https://example.com/other'}
        
        id1 = nuclei_runner._generate_finding_id(finding1)
        id2 = nuclei_runner._generate_finding_id(finding2)
        id3 = nuclei_runner._generate_finding_id(finding3)
        
        # All IDs should be different
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3
        
        # Same finding should generate same ID
        id1_again = nuclei_runner._generate_finding_id(finding1)
        assert id1 == id1_again