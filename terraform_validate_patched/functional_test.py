import re
import os
import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import terraform_validate_patched as t

class TestValidatorFunctional(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)))

    def error_list_format(self,error_list):
        if type(error_list) is not list:
            error_list = [error_list]
        regex = "\n".join(map(re.escape,error_list))
        return "^{0}$".format(regex)

    def test_resource(self):
        validator = t.Validator(os.path.join(self.path,"fixtures/resource"))
        validator.resources('aws_instance').property('value').should_equal(1)
        expected_error = self.error_list_format([
            "[aws_instance.bar.value] should be '2'. Is: '1'",
            "[aws_instance.foo.value] should be '2'. Is: '1'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('value').should_equal(2)

    def test_nested_resource(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources('aws_instance').property('nested_resource').property('value').should_equal(1)
        expected_error = self.error_list_format("[aws_instance.foo.nested_resource.value] should be '2'. Is: '1'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('nested_resource').property('value').should_equal(2)

    def test_resource_not_equals(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.resources('aws_instance').property('value').should_not_equal(0)
        expected_error = self.error_list_format([
            "[aws_instance.bar.value] should not be '1'. Is: '1'",
            "[aws_instance.foo.value] should not be '1'. Is: '1'"
        ])
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').property('value').should_not_equal(1)

    def test_nested_resource_not_equals(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources('aws_instance').property('nested_resource').property('value').should_not_equal(0)
        expected_error = self.error_list_format("[aws_instance.foo.nested_resource.value] should not be '1'. Is: '1'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').property('nested_resource').property('value').should_not_equal(1)

    def test_resource_required_properties_with_list_input(self):
        required_properties = ['value', 'value2']
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.resources('aws_instance').should_have_properties(required_properties)
        required_properties = ['value', 'value2', 'abc123','def456']
        expected_error = self.error_list_format([
            "[aws_instance.bar] should have property: 'abc123'",
            "[aws_instance.bar] should have property: 'def456'",
            "[aws_instance.foo] should have property: 'abc123'",
            "[aws_instance.foo] should have property: 'def456'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').should_have_properties(required_properties)

    def test_resource_required_properties_with_string_input(self):
        required_property = 'value'
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.resources('aws_instance').should_have_properties(required_property)

    def test_resource_excluded_properties_with_list_input(self):
        excluded_properties = ['value', 'value2']
        non_excluded_properties = ['value3','value4']
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.resources('aws_instance').should_not_have_properties(non_excluded_properties)
        expected_error =self.error_list_format([
            "[aws_instance.bar] should not have property: 'value'",
            "[aws_instance.bar] should not have property: 'value2'",
            "[aws_instance.foo] should not have property: 'value'",
            "[aws_instance.foo] should not have property: 'value2'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').should_not_have_properties(excluded_properties)

    def test_resource_excluded_properties_with_string_input(self):
        excluded_property = 'value'
        non_excluded_property = 'value3'
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.resources('aws_instance').should_not_have_properties(non_excluded_property)
        expected_error = self.error_list_format([
            "[aws_instance.bar] should not have property: 'value'",
            "[aws_instance.foo] should not have property: 'value'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').should_not_have_properties(excluded_property)

    def test_nested_resource_required_properties_with_list_input(self):
        required_properties = ['value','value2']
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources('aws_instance').property('nested_resource').should_have_properties(required_properties)
        required_properties = ['value', 'value2', 'abc123', 'def456']
        expected_error = self.error_list_format([
            "[aws_instance.foo.nested_resource] should have property: 'abc123'",
            "[aws_instance.foo.nested_resource] should have property: 'def456'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('nested_resource').should_have_properties(required_properties)

    def test_nested_resource_required_properties_with_string_input(self):
        required_property = 'value'
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources('aws_instance').property('nested_resource').should_have_properties(required_property)
        required_property = 'def456'
        expected_error = self.error_list_format([
            "[aws_instance.foo.nested_resource] should have property: 'def456'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('nested_resource').should_have_properties(
                required_property)

    def test_nested_resource_excluded_properties_with_list_input(self):
        excluded_properties = ['value', 'value2']
        non_excluded_properties = ['value3','value4']
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources('aws_instance').property('nested_resource').should_not_have_properties(non_excluded_properties)
        expected_error = self.error_list_format([
            "[aws_instance.foo.nested_resource] should not have property: 'value'",
            "[aws_instance.foo.nested_resource] should not have property: 'value2'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('nested_resource').should_not_have_properties(excluded_properties)

    def test_nested_resource_excluded_properties_with_string_input(self):
        excluded_property = 'value'
        non_excluded_property = 'value3'
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources('aws_instance').property('nested_resource').should_not_have_properties(
            non_excluded_property)
        expected_error = self.error_list_format([
            "[aws_instance.foo.nested_resource] should not have property: 'value'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('nested_resource').should_not_have_properties(
                excluded_property)

    def test_resource_property_value_matches_regex(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.resources('aws_instance').property('value').should_match_regex('[0-9]')
        expected_error = self.error_list_format([
            "[aws_instance.bar.value] should match regex '[a-z]'",
            "[aws_instance.foo.value] should match regex '[a-z]'"
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('value').should_match_regex('[a-z]')

    def test_nested_resource_property_value_matches_regex(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources('aws_instance').property('nested_resource').property('value').should_match_regex('[0-9]')
        expected_error = self.error_list_format("[aws_instance.foo.nested_resource.value] should match regex '[a-z]'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('nested_resource').property('value').should_match_regex('[a-z]')

    def test_resource_property_invalid_json(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/invalid_json"))
        expected_error = self.error_list_format("[aws_s3_bucket.invalidjson.policy] is not valid json")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_s3_bucket').property('policy').should_contain_valid_json()

    def test_variable_substitution(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/variable_substitution"))
        validator.enable_variable_expansion()
        validator.resources('aws_instance').property('value').should_equal(1)
        expected_error = self.error_list_format("[aws_instance.foo.value] should be '2'. Is: '1'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').property('value').should_equal(2)
        validator.disable_variable_expansion()
        validator.resources('aws_instance').property('value').should_equal('${var.test_variable}')

    def test_missing_variable_substitution(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/missing_variable"))
        validator.enable_variable_expansion()
        expected_error = self.error_list_format("There is no Terraform variable 'missing'")
        with self.assertRaisesRegexp(t.TerraformVariableException, expected_error):
            validator.resources('aws_instance').property('value').should_equal(1)

    # def test_missing_required_nested_resource_fails(self):
    #     validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
    #     self.assertRaises(AssertionError,validator.resources('aws_instance').property('tags').property('encrypted').should_equal(1))

    def test_properties_on_nonexistant_resource_type(self):
        required_properties = ['value', 'value2']
        validator = t.Validator(os.path.join(self.path, "fixtures/missing_variable"))
        validator.resources('aws_rds_instance').property('nested_resource').should_have_properties(required_properties)

    def test_searching_for_property_on_nonexistant_nested_resource(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.error_if_property_missing()
        expected_error = self.error_list_format(
                                                [
                                                    "[aws_instance.bar] should have property: 'tags'",
                                                    "[aws_instance.foo] should have property: 'tags'"
                                                ]
                                                )
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('tags').property('tagname').should_equal(1)

    def test_searching_for_property_value_using_regex(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/regex_variables"))
        validator.resources('aws_instance').find_property('^CPM_Service_[A-Za-z]+$').should_equal(1)
        expected_error = self.error_list_format("[aws_instance.foo.CPM_Service_wibble] should be '2'. Is: '1'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').find_property('^CPM_Service_[A-Za-z]+$').should_equal(2)

    def test_searching_for_nested_property_value_using_regex(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/regex_nested_variables"))
        validator.resources('aws_instance').property('tags').find_property('^CPM_Service_[A-Za-z]+$').should_equal(1)
        expected_error = self.error_list_format("[aws_instance.foo.tags.CPM_Service_wibble] should be '2'. Is: '1'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').property('tags').find_property('^CPM_Service_[A-Za-z]+$').should_equal(2)

    def test_resource_type_list(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/resource"))
        validator.resources(['aws_instance','aws_elb']).property('value').should_equal(1)
        expected_error = self.error_list_format([
                            "[aws_elb.buzz.value] should be '2'. Is: '1'",
                            "[aws_instance.bar.value] should be '2'. Is: '1'",
                            "[aws_instance.foo.value] should be '2'. Is: '1'"
                          ])
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources(['aws_instance','aws_elb']).property('value').should_equal(2)


    def test_nested_resource_type_list(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/nested_resource"))
        validator.resources(['aws_instance', 'aws_elb']).property('tags').property('value').should_equal(1)
        expected_error = self.error_list_format([
            "[aws_elb.foo.tags.value] should be '2'. Is: '1'",
            "[aws_instance.foo.tags.value] should be '2'. Is: '1'"
        ])
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources(['aws_instance', 'aws_elb']).property('tags').property('value').should_equal(2)

    def test_invalid_terraform_syntax(self):
        self.assertRaises(t.TerraformSyntaxException, t.Validator,os.path.join(self.path, "fixtures/invalid_syntax"))

    def test_multiple_variable_substitutions(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/multiple_variables"))
        validator.enable_variable_expansion()
        validator.resources('aws_instance').property('value').should_equal(12)
        expected_error = self.error_list_format("[aws_instance.foo.value] should be '21'. Is: '12'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').property('value').should_equal(21)

    def test_nested_multiple_variable_substitutions(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/multiple_variables"))
        validator.enable_variable_expansion()
        validator.resources('aws_instance').property('value_block').property('value').should_equal(21)
        expected_error = self.error_list_format("[aws_instance.foo.value_block.value] should be '12'. Is: '21'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').property('value_block').property('value').should_equal(12)

    def test_variable_expansion(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/variable_expansion"))
        validator.resources('aws_instance').property('value').should_equal('${var.bar}')
        expected_error = self.error_list_format("[aws_instance.foo.value] should be '${bar.var}'. Is: '${var.bar}'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources('aws_instance').property('value').should_equal('${bar.var}')

    def test_resource_name_matches_regex(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/resource_name"))

        validator.resources('aws_foo').name_should_match_regex('^[a-z0-9_]*$')
        expected_error = self.error_list_format("[aws_instance.TEST_RESOURCE] name should match regex '^[a-z0-9_]*$'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources('aws_instance').name_should_match_regex('^[a-z0-9_]*$')

    def test_variable_has_default_value(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/default_variable"))
        expected_error = self.error_list_format("Variable 'bar' should have a default value")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.variable('bar').default_value_exists()

    def test_variable_default_value_equals(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/default_variable"))
        expected_error = self.error_list_format("Variable 'bar' should have a default value of 2. Is: None")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.variable('bar').default_value_equals(2)
        validator.variable('bar').default_value_equals(None)

    def test_variable_default_value_matches_regex(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/default_variable"))
        expected_error = self.error_list_format("Variable 'bizz' should have a default value that matches regex '^123'. Is: abc")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.variable('bizz').default_value_matches_regex('^123')

    def test_no_exceptions_raised_when_no_resources_present(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/no_resources"))
        validator.resources('aws_instance').property('value').should_equal(1)

    def test_lowercase_formatting_in_variable_substitution(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/lower_format_variable"))
        validator.enable_variable_expansion()

        validator.resources('aws_instance').property('value').should_equal('abc')
        validator.resources('aws_instance2').property('value').should_equal('abcDEF')

    def test_parsing_variable_with_unimplemented_interpolation_function(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/unimplemented_interpolation"))
        validator.enable_variable_expansion()
        self.assertRaises(t.TerraformUnimplementedInterpolationException, validator.resources('aws_instance').property('value').should_equal,'abc')

    def test_boolean_equal(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/boolean_compare"))
        values = [True, "true", "True"]

        for i in range(1,5):
            for value in values:
                validator.resources("aws_db_instance").property("storage_encrypted{0}".format(i)).should_equal(value)

    def test_list_should_contain(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/list_variable"))
        validator.resources("datadog_monitor").property("tags").list_should_contain(['baz:biz'])
        expected_error = self.error_list_format([
            "[datadog_monitor.bar.tags] '['baz:biz', 'foo:bar']' should contain '['too:biz']'.",
            "[datadog_monitor.foo.tags] '['baz:biz']' should contain '['too:biz']'."
        ])
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("datadog_monitor").property("tags").list_should_contain('too:biz')

    def test_list_should_not_contain(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/list_variable"))
        validator.resources("datadog_monitor").property("tags").list_should_not_contain(['foo:baz'])
        validator.resources("datadog_monitor").property("tags").list_should_not_contain('foo:baz')
        expected_error = self.error_list_format("[datadog_monitor.bar.tags] '['baz:biz', 'foo:bar']' should not contain '['foo:bar']'.")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("datadog_monitor").property("tags").list_should_not_contain('foo:bar')

    def test_property_list_scenario(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/list_property"))
        validator.error_if_property_missing()

        validator.resources("aws_autoscaling_group").property("tag").property('propagate_at_launch').should_equal("True")
        validator.resources("aws_autoscaling_group").property("tag").property('propagate_at_launch').should_equal(True)

    def test_encryption_scenario(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/enforce_encrypted"))
        validator.error_if_property_missing()

        validator.resources("aws_db_instance_valid").property("storage_encrypted").should_equal("True")
        validator.resources("aws_db_instance_valid").property("storage_encrypted").should_equal(True)
        validator.resources("aws_db_instance_invalid").should_have_properties("storage_encrypted")

        expected_error = self.error_list_format("[aws_db_instance_invalid.foo2.storage_encrypted] should be 'True'. Is: 'False'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("aws_db_instance_invalid").property("storage_encrypted").should_equal("True")
        expected_error = self.error_list_format("[aws_db_instance_invalid2.foo3] should have property: 'storage_encrypted'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("aws_db_instance_invalid2").property("storage_encrypted")

        validator.resources("aws_instance_valid").property('ebs_block_device').property("encrypted").should_equal("True")
        validator.resources("aws_instance_valid").property('ebs_block_device').property("encrypted").should_equal(True)

        expected_error = self.error_list_format("[aws_instance_invalid.bizz2] should have property: 'encrypted'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("aws_instance_invalid").should_have_properties("encrypted")

        expected_error = self.error_list_format("[aws_instance_invalid.bizz2.ebs_block_device.encrypted] should be 'True'. Is: 'False'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("aws_instance_invalid").property('ebs_block_device').property("encrypted").should_equal("True")

        expected_error = self.error_list_format("[aws_instance_invalid2.bizz3] should have property: 'storage_encrypted'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("aws_instance_invalid2").should_have_properties("storage_encrypted")

        expected_error = self.error_list_format("[aws_instance_invalid2.bizz3.ebs_block_device] should have property: 'encrypted'")
        with self.assertRaisesRegexp(AssertionError, expected_error):
            validator.resources("aws_instance_invalid2").property('ebs_block_device').property("encrypted")

        validator.resources("aws_ebs_volume_valid").property("encrypted").should_equal("True")
        validator.resources("aws_ebs_volume_valid").property("encrypted").should_equal(True)
        validator.resources("aws_ebs_volume_invalid").should_have_properties("encrypted")

        expected_error = self.error_list_format("[aws_ebs_volume_invalid.bar2.encrypted] should be 'True'. Is: 'False'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources("aws_ebs_volume_invalid").property("encrypted").should_equal("True")

        expected_error = self.error_list_format("[aws_ebs_volume_invalid2.bar3] should have property: 'encrypted'")
        with self.assertRaisesRegexp(AssertionError,expected_error):
            validator.resources("aws_ebs_volume_invalid2").should_have_properties("encrypted")
            validator.resources("aws_ebs_volume_invalid2").property("encrypted")

    def test_with_property(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/with_property"))

        expected_error = self.error_list_format("[aws_s3_bucket.private_bucket.policy] is not valid json")

        private_buckets = validator.resources("aws_s3_bucket").with_property("acl", "private")

        with self.assertRaisesRegexp(AssertionError, expected_error):
            private_buckets.property("policy").should_contain_valid_json()

    def test_with_nested_property(self):
        validator = t.Validator(os.path.join(self.path, "fixtures/with_property"))

        expected_error = self.error_list_format("[aws_s3_bucket.tagged_bucket.policy] is not valid json")

        tagged_buckets = validator.resources("aws_s3_bucket").with_property("tags", ".*'CustomTag':.*'CustomValue'.*")

        with self.assertRaisesRegexp(AssertionError, expected_error):
            tagged_buckets.property("policy").should_contain_valid_json()
