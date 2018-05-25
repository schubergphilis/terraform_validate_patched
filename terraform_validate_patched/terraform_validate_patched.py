import hcl
import os
import re
import warnings
import logging
import json

# This is the main prefix used for logging
LOGGER_BASENAME = '''TerraformValidate'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


def is_test_skipped(resource):
    def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
        return '\n\n{}:{}\n\n'.format(category.__name__, message)
    warnings.formatwarning = warning_on_one_line
    skip_tag = 'skip-testing'
    if resource.config.get('tags', {}).get('skip_testing') is not None:
        message_ = ('The tag "skip_testing" is deprecated. '
                    'Please use "skip-testing". Resource: {}').format(resource.name)
        warnings.simplefilter("always")
        warnings.warn(message_ , DeprecationWarning)
        skip_tag = 'skip_testing'
    return True if resource.config.get('tags', {}).get(skip_tag, False) == 'true' else False


class TerraformSyntaxException(Exception):
    pass


class TerraformVariableException(Exception):
    pass


class TerraformUnimplementedInterpolationException(Exception):
    pass


class TerraformVariableParser:

    def __init__(self, string):
        self.string = string
        self.functions = []
        self.variable = ""
        self.state = 0
        self.index = 0

    def parse(self):
        while self.index < len(self.string):
            if self.state == 0:
                if self.string[self.index:self.index + 3] == "var":
                    self.index += 3
                    self.state = 1
                else:
                    self.state = 3
                    temp_function = ""
            if self.state == 1:
                temp_var = ""
                while True:
                    self.index += 1
                    if self.index == len(self.string) or self.string[self.index] == ")":
                        self.variable = temp_var
                        self.state = 2
                        break;
                    else:
                        temp_var += self.string[self.index]
            if self.state == 2:
                self.index += 1
            if self.state == 3:
                if self.string[self.index] == "(":
                    self.state = 0
                    self.functions.append(temp_function)
                else:
                    temp_function += self.string[self.index]
                self.index += 1

class TerraformPropertyList:

    def __init__(self, validator):
        self.properties = []
        self.validator = validator

    def tfproperties(self):
        return self.properties

    def property(self, property_name):
        errors = []
        result = TerraformPropertyList(self.validator)
        for property in self.properties:
            def _check_prop(prop_value):
                if property_name in prop_value.keys():
                    result.properties.append(TerraformProperty(property.resource_type,
                                                               "{0}.{1}".format(property.resource_name,
                                                                                property.property_name),
                                                               property_name,
                                                               prop_value[property_name]))
                elif self.validator.raise_error_if_property_missing:
                    errors.append("[{0}.{1}] should have property: '{2}'".format(property.resource_type,
                                                                                 "{0}.{1}".format(
                                                                                     property.resource_name,
                                                                                     property.property_name),
                                                                                 property_name))

            if isinstance(property.property_value, list):
                for prop in property.property_value:
                    _check_prop(prop)
            else:
                _check_prop(property.property_value)

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

        return result

    def should_equal(self, expected_value):
        errors = []
        for property in self.properties:

            actual_property_value = self.validator.substitute_variable_values_in_string(property.property_value)

            expected_value = self.int2str(expected_value)
            actual_property_value = self.int2str(actual_property_value)
            expected_value = self.bool2str(expected_value)
            actual_property_value = self.bool2str(actual_property_value)

            if actual_property_value != expected_value:
                errors.append("[{0}.{1}.{2}] should be '{3}'. Is: '{4}'".format(property.resource_type,
                                                                                property.resource_name,
                                                                                property.property_name,
                                                                                expected_value,
                                                                                actual_property_value))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def should_not_equal(self, expected_value):
        errors = []
        for property in self.properties:

            actual_property_value = self.validator.substitute_variable_values_in_string(property.property_value)

            actual_property_value = self.int2str(actual_property_value)
            expected_value = self.int2str(expected_value)
            expected_value = self.bool2str(expected_value)
            actual_property_value = self.bool2str(actual_property_value)

            if actual_property_value == expected_value:
                errors.append("[{0}.{1}.{2}] should not be '{3}'. Is: '{4}'".format(property.resource_type,
                                                                                    property.resource_name,
                                                                                    property.property_name,
                                                                                    expected_value,
                                                                                    actual_property_value))

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def list_should_contain(self, values_list):
        errors = []

        if type(values_list) is not list:
            values_list = [values_list]

        for property in self.properties:

            actual_property_value = self.validator.substitute_variable_values_in_string(property.property_value)
            values_missing = []
            for value in values_list:
                if value not in actual_property_value:
                    values_missing.append(value)

            if len(values_missing) != 0:
                if type(actual_property_value) is list:
                    actual_property_value = [str(x) for x in actual_property_value]  # fix 2.6/7
                errors.append("[{0}.{1}.{2}] '{3}' should contain '{4}'.".format(property.resource_type,
                                                                                 property.resource_name,
                                                                                 property.property_name,
                                                                                 actual_property_value,
                                                                                 values_missing))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def list_should_not_contain(self, values_list):
        errors = []

        if type(values_list) is not list:
            values_list = [values_list]

        for property in self.properties:

            actual_property_value = self.validator.substitute_variable_values_in_string(property.property_value)
            values_missing = []
            for value in values_list:
                if value in actual_property_value:
                    values_missing.append(value)

            if len(values_missing) != 0:
                if type(actual_property_value) is list:
                    actual_property_value = [str(x) for x in actual_property_value]  # fix 2.6/7
                errors.append("[{0}.{1}.{2}] '{3}' should not contain '{4}'.".format(property.resource_type,
                                                                                     property.resource_name,
                                                                                     property.property_name,
                                                                                     actual_property_value,
                                                                                     values_missing))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def should_have_properties(self, properties_list):
        errors = []

        if type(properties_list) is not list:
            properties_list = [properties_list]

        for property in self.properties:
            property_names = property.property_value.keys()
            for required_property_name in properties_list:
                if required_property_name not in property_names:
                    errors.append("[{0}.{1}.{2}] should have property: '{3}'".format(property.resource_type,
                                                                                     property.resource_name,
                                                                                     property.property_name,
                                                                                     required_property_name))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def should_not_have_properties(self, properties_list):
        errors = []

        if type(properties_list) is not list:
            properties_list = [properties_list]

        for property in self.properties:
            property_names = property.property_value.keys()
            for excluded_property_name in properties_list:
                if excluded_property_name in property_names:
                    errors.append(
                        "[{0}.{1}.{2}] should not have property: '{3}'".format(property.resource_type,
                                                                               property.resource_name,
                                                                               property.property_name,
                                                                               excluded_property_name))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def find_property(self, regex):
        list = TerraformPropertyList(self.validator)
        for property in self.properties:
            for nested_property in property.property_value:
                if self.validator.matches_regex_pattern(nested_property, regex):
                    list.properties.append(TerraformProperty(property.resource_type,
                                                             "{0}.{1}".format(property.resource_name,
                                                                              property.property_name),
                                                             nested_property,
                                                             property.property_value[nested_property]))
        return list

    def should_match_regex(self, regex):
        errors = []
        for property in self.properties:
            actual_property_value = self.validator.substitute_variable_values_in_string(property.property_value)
            if not self.validator.matches_regex_pattern(actual_property_value, regex):
                errors.append("[{0}.{1}] should match regex '{2}'".format(property.resource_type,
                                                                          "{0}.{1}".format(property.resource_name,
                                                                                           property.property_name),
                                                                          regex))

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def should_contain_valid_json(self):
        errors = []
        for property in self.properties:
            actual_property_value = self.validator.substitute_variable_values_in_string(property.property_value)
            try:
                json_object = json.loads(actual_property_value)
            except:
                errors.append("[{0}.{1}.{2}] is not valid json".format(property.resource_type, property.resource_name,
                                                                       property.property_name))

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def bool2str(self, bool):
        if str(bool).lower() in ["true"]:
            return "True"
        if str(bool).lower() in ["false"]:
            return "False"
        return bool

    def int2str(self, property_value):
        if type(property_value) is int:
            property_value = str(property_value)
        return property_value


class TerraformProperty:

    def __init__(self, resource_type, resource_name, property_name, property_value):
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.property_name = property_name
        self.property_value = property_value

    def get_property_value(self, validator):
        return validator.substitute_variable_values_in_string(self.property_value)


class TerraformResource:

    def __init__(self, type, name, config):
        self.type = type
        self.name = name
        self.config = config


class TerraformResourceList:

    def __init__(self, validator, resource_types, resources):
        logger_name = u'{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                                suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self.resource_list = []

        if type(resource_types) is not list:
            all_resource_types = list(resources.keys())
            regex = resource_types
            resource_types = []
            for resource_type in all_resource_types:
                if validator.matches_regex_pattern(resource_type, regex):
                    resource_types.append(resource_type)

        for resource_type in resource_types:
            if resource_type in resources.keys():
                for resource in resources[resource_type]:
                    resource_ = TerraformResource(resource_type, resource, resources[resource_type][resource])
                    if not is_test_skipped(resource_):
                        self.resource_list.append(resource_)
                    else:
                        self._logger.warning('Skipping resource {}/{} due to user override tag'.format(resource_type,
                                                                                                      resource))

        self.resource_types = resource_types
        self.validator = validator

    def property(self, property_name):
        errors = []
        list = TerraformPropertyList(self.validator)
        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                if property_name in resource.config.keys():
                    list.properties.append(
                        TerraformProperty(resource.type, resource.name, property_name, resource.config[property_name]))
                elif self.validator.raise_error_if_property_missing:
                    errors.append(
                        "[{0}.{1}] should have property: '{2}'".format(resource.type, resource.name, property_name))

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

        return list

    def find_property(self, regex):
        list = TerraformPropertyList(self.validator)
        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                for property in resource.config:
                    if self.validator.matches_regex_pattern(property, regex):
                        list.properties.append(TerraformProperty(resource.type,
                                                                 resource.name,
                                                                 property,
                                                                 resource.config[property]))
        return list

    def with_property(self, property_name, regex):
        list = TerraformResourceList(self.validator, self.resource_types, {})

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                for property in resource.config:
                    if (property == property_name):
                        tf_property = TerraformProperty(resource.type, resource.name, property_name,
                                                        resource.config[property_name])
                        actual_property_value = self.validator.substitute_variable_values_in_string(
                            tf_property.property_value)
                        if self.validator.matches_regex_pattern(actual_property_value, regex):
                            list.resource_list.append(resource)

        return list

    def should_have_properties(self, properties_list):
        errors = []

        if type(properties_list) is not list:
            properties_list = [properties_list]

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                property_names = resource.config.keys()
                for required_property_name in properties_list:
                    if required_property_name not in property_names:
                        errors.append(
                            "[{0}.{1}] should have property: '{2}'".format(resource.type,
                                                                           resource.name,
                                                                           required_property_name))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def should_not_have_properties(self, properties_list):
        errors = []

        if type(properties_list) is not list:
            properties_list = [properties_list]

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                property_names = resource.config.keys()
                for excluded_property_name in properties_list:
                    if excluded_property_name in property_names:
                        errors.append(
                            "[{0}.{1}] should not have property: '{2}'".format(resource.type,
                                                                               resource.name,
                                                                               excluded_property_name))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def name_should_match_regex(self, regex):
        errors = []
        for resource in self.resource_list:
            if not self.validator.matches_regex_pattern(resource.name, regex):
                errors.append("[{0}.{1}] name should match regex '{2}'".format(resource.type, resource.name, regex))

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))


class TerraformVariable:

    def __init__(self, validator, name, value):
        self.validator = validator
        self.name = name
        self.value = value

    def default_value_exists(self):
        errors = []
        if self.value == None:
            errors.append("Variable '{0}' should have a default value".format(self.name))

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def default_value_equals(self, expected_value):
        errors = []

        if self.value != expected_value:
            errors.append("Variable '{0}' should have a default value of {1}. Is: {2}".format(self.name,
                                                                                              expected_value,
                                                                                              self.value))
        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))

    def default_value_matches_regex(self, regex):
        errors = []
        if not self.validator.matches_regex_pattern(self.value, regex):
            errors.append(
                "Variable '{0}' should have a default value that matches regex '{1}'. Is: {2}".format(self.name, regex,
                                                                                                      self.value))

        if len(errors) > 0:
            raise AssertionError("\n".join(sorted(errors)))


class Validator:

    def __init__(self, path=None):
        logger_name = u'{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                                suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self.variable_expand = False
        self.raise_error_if_property_missing = False
        if type(path) is not dict:
            if path is not None:
                self.terraform_config = self.parse_terraform_directory(path)
        else:
            self.terraform_config = path

    def resources(self, type):
        if 'resource' not in self.terraform_config.keys():
            resources = {}
        else:
            resources = self.terraform_config['resource']

        return TerraformResourceList(self, type, resources)

    def variable(self, name):
        return TerraformVariable(self, name, self.get_terraform_variable_value(name))

    def enable_variable_expansion(self):
        self.variable_expand = True

    def disable_variable_expansion(self):
        self.variable_expand = False

    def error_if_property_missing(self):
        self.raise_error_if_property_missing = True

    def read_terraform_file(self, fullpath):
        with open(fullpath) as fp:
            new_terraform = fp.read()
        return new_terraform

    # def get_git_module(self, source_string):
    #     ### In here we clone the git module.
    #     ### Best to do it to a temp path.
    #     ### Create temp path using the name of the repo and ref.
    #     ### Then pass back the temp path as a string
    #     ### This, along with the validator gets run each time
    #     ### a test is run.  Might not seem efficient,
    #     ### but if not done this way, it could cause issues
    #     ### with incorrect or outdated data being kept around.
    #     ### In the future, I would like to turn some of these parts
    #     ### into functions to make them reusable for other repo types.
    #
    #     if source_string.startswith("git::"):  ## pull apart the source string to make it a directory name
    #         source_string = source_string[5:]
    #     if "?" in source_string:  ## if theres a ?ref=<branch or commit>, use that for the dir name.
    #         source, refs = source_string.split("?")
    #     else:
    #         source = source_string
    #     repo_temp_dir = source.split("/")[-1]
    #     if os.name == 'nt':  ## This is the one place where my code is different for windows.
    #         directory = "c:\\temp\\terraform_validate\\" + repo_temp_dir
    #     else:
    #         directory = '/tmp/terraform_validate/' + repo_temp_dir
    #     if 'refs' in locals():
    #         refs = refs.split('=')[-1]
    #         if "//" in refs:
    #             refs = refs.split('//')[0]
    #         directory = directory + '-' + refs
    #     try:
    #         os.stat(directory)
    #         shutil.rmtree(directory, ignore_errors=True)  ## clean slate, unless a unique directory.
    #     except:
    #         pass
    #     os.makedirs(directory)
    #     repo = git.Git(directory)
    #     repo.clone(source, directory)  ## by default, this checks out master.
    #     if 'refs' in locals():
    #         repo.checkout(refs)  ## if a ref was specified, check it out.
    #     return directory
    #
    # def check_terraform_for_modules(self, new_terraform):
    #
    #     ## terraform itself uses a git getter which essentially just uses the system's git
    #     ## in order to perform the get of repo and any submodules.
    #     ## since this is the method used, I am assuming that a similar method is acceptable here.
    #     ## we have gitpython; which makes similar assumptions to terraform.
    #
    #     modules_to_process = []
    #     terra_dictionary = hcl.loads(new_terraform)
    #     if ("module" in terra_dictionary):
    #         for module in terra_dictionary['module'].values():
    #             if (isinstance(module, dict)):
    #                 for key, value in module.items():
    #                     if ("source" in key):
    #                         if ((value.startswith(".")) or (value.startswith("/"))):
    #                             modules_to_process.append(value)
    #                         if '.git' or '::git' in (value):
    #                             modules_to_process.append(self.get_git_module(value))
    #     return modules_to_process

    # def parse_terraform_directory(self,path):
    #     ## It looks like we are repeating ourselves.  This is done to first process the initial directory
    #     ## and then gain the details for the modules.  Future modification may DRY this by separating
    #     ## it into different functions.  Alas, I have no more time to work on this.
    #
    #     terraform_string = ""
    #     for directory, subdirectories, files in os.walk(path):
    #         for file in files:
    #             if (file.endswith(".tf")):
    #                 new_terraform = self.read_terraform_file(directory+"/"+file)
    #                 try:
    #                     hcl.loads(new_terraform)
    #                 except ValueError as e:
    #                     raise TerraformSyntaxException("Invalid terraform configuration in {0}\n{1}".format(os.path.join(directory,file),e))
    #                 modules_to_process = self.check_terraform_for_modules(new_terraform)
    #                 terraform_string += new_terraform
    #                 if (modules_to_process is not None):
    #                     for module_directory in modules_to_process:
    #                         for mod_directory, mod_subdirectories, mod_files in os.walk(module_directory):
    #                             for mod_file in mod_files:
    #                                 if (mod_file.endswith(".tf")):
    #                                     module_terraform = self.read_terraform_file(mod_directory+"/"+mod_file)
    #                                     try:
    #                                         hcl.loads(module_terraform)
    #                                     except ValueError as e:
    #
    #                                         raise TerraformSyntaxException("Invalid terraform configuration in {0}\n{1}".format(os.path.join(mod_directory,mod_file),e))
    #
    #                     terraform_string += new_terraform
    #     terraform = hcl.loads(terraform_string)
    #     return terraform

    def parse_terraform_directory(self, path):
        terraform_string = ""
        for directory, subdirectories, files in os.walk(path):
            for ifile in files:
                if ifile.endswith(".tf"):
                    with open(os.path.join(directory, ifile)) as fp:
                        new_terraform = fp.read()
                        try:
                            hcl.loads(new_terraform)
                        except ValueError:
                            self._logger.debug('Terraform plan {} is empty, skipping'.format(ifile))
                            continue
                        terraform_string += new_terraform
        terraform = hcl.loads(terraform_string)
        return terraform

    def get_terraform_resources(self, name, resources):
        if name not in resources.keys():
            return []
        return self.convert_to_list(resources[name])

    def matches_regex_pattern(self, variable, regex):
        return not (self.get_regex_matches(regex, variable) is None)

    def get_regex_matches(self, regex, variable):
        if regex[-1:] != "$":
            regex = regex + "$"

        if regex[0] != "^":
            regex = "^" + regex

        variable = str(variable)
        if '\n' in variable:
            return re.match(regex, variable, re.DOTALL)
        return re.match(regex, variable)

    def get_terraform_variable_value(self, variable):
        if ('variable' not in self.terraform_config.keys()) or (
                variable not in self.terraform_config['variable'].keys()):
            raise TerraformVariableException("There is no Terraform variable '{0}'".format(variable))
        if 'default' not in self.terraform_config['variable'][variable].keys():
            return None
        return self.terraform_config['variable'][variable]['default']

    def substitute_variable_values_in_string(self, s):
        if self.variable_expand:
            if not isinstance(s, dict):
                for variable in self.list_terraform_variables_in_string(s):
                    a = TerraformVariableParser(variable)
                    a.parse()
                    variable_default_value = self.get_terraform_variable_value(a.variable)
                    if variable_default_value != None:
                        for function in a.functions:
                            if function == "lower":
                                variable_default_value = variable_default_value.lower()
                            elif function == "upper":
                                variable_default_value = variable_default_value.upper()
                            else:
                                raise TerraformUnimplementedInterpolationException(
                                    "The interpolation function '{0}' has not been implemented in Terraform Validator yet. Suggest you run disable_variable_expansion().".format(
                                        function))
                        s = s.replace("${" + variable + "}", variable_default_value)
        return s

    def list_terraform_variables_in_string(self, s):
        return re.findall('\${(.*?)}', str(s))

    def convert_to_list(self, nested_resources):
        if not type(nested_resources) == list:
            nested_resources = [nested_resources]
        return nested_resources
