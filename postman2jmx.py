#!/usr/bin/env python3
import json
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

def convert_postman_to_jmx(postman_file, output_file, environment_file=None):
    """
    Converts a Postman collection JSON file to a JMeter JMX file.

    Args:
        postman_file (str): Path to the Postman collection JSON file.
        output_file (str): Path where the JMeter JMX file will be saved.
        environment_file (str, optional): Path to the Postman environment JSON file.
                                          If provided, environment variables will be added.
    """
    # Load Postman collection
    with open(postman_file, 'r') as f:
        collection = json.load(f)

    # Load Postman environment if provided
    environment_vars = []
    if environment_file:
        try:
            with open(environment_file, 'r') as f_env:
                environment_data = json.load(f_env)
                if 'values' in environment_data:
                    # Filter for enabled variables from the environment
                    environment_vars = [v for v in environment_data['values'] if v.get('enabled', True)]
        except FileNotFoundError:
            print(f"Warning: Environment file '{environment_file}' not found. Skipping environment variables.")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse environment file '{environment_file}'. Skipping environment variables.")


    # Create JMX root structure
    jmeter_test_plan = ET.Element('jmeterTestPlan', version="1.2", properties="5.0", jmeter="5.2.1")
    hash_tree = ET.SubElement(jmeter_test_plan, 'hashTree')

    # Create Test Plan
    test_plan = ET.SubElement(hash_tree, 'TestPlan', {
        'guiclass': 'TestPlanGui',
        'testclass': 'TestPlan',
        'testname': 'Postman Collection Import',
        'enabled': 'true'
    })
    ET.SubElement(test_plan, 'boolProp', name="TestPlan.functional_mode").text = 'false'
    ET.SubElement(test_plan, 'stringProp', name="TestPlan.comments")
    ET.SubElement(test_plan, 'boolProp', name="TestPlan.serialize_threadgroups").text = 'false'
    ET.SubElement(test_plan, 'stringProp', name="TestPlan.user_define_classpath")

    # Add default user defined variables to the Test Plan (can be empty)
    element_prop = ET.SubElement(test_plan, 'elementProp', {
        'name': 'TestPlan.user_defined_variables',
        'elementType': 'Arguments'
    })
    ET.SubElement(element_prop, 'collectionProp', name="Arguments.arguments")

    hash_tree2 = ET.SubElement(hash_tree, 'hashTree')

    # Create Thread Group
    thread_group = ET.SubElement(hash_tree2, 'ThreadGroup', {
        'guiclass': 'ThreadGroupGui',
        'testclass': 'ThreadGroup',
        'testname': collection.get('info', {}).get('name', 'Postman Requests'),
        'enabled': 'true'
    })

    element_prop = ET.SubElement(thread_group, 'elementProp', {
        'name': 'ThreadGroup.main_controller',
        'elementType': 'LoopController',
        'guiclass': 'LoopControlPanel',
        'testclass': 'LoopController',
        'enabled': 'true'
    })
    ET.SubElement(element_prop, 'boolProp', name="LoopController.continue_forever").text = 'false'
    ET.SubElement(element_prop, 'stringProp', name="LoopController.loops").text = '1'

    ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.num_threads").text = '1'
    ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.ramp_time").text = '1'
    ET.SubElement(thread_group, 'boolProp', name="ThreadGroup.scheduler").text = 'false'
    ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.duration").text = '0'
    ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.delay").text = '0'
    ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.on_sample_error").text = 'continue'
    ET.SubElement(thread_group, 'boolProp', name="ThreadGroup.same_user_on_next_iteration").text = 'true'

    hash_tree3 = ET.SubElement(hash_tree2, 'hashTree')

    # Process collection variables
    if 'variable' in collection:
        add_user_defined_variables(collection['variable'], hash_tree3, name="Collection Variables")

    # Process environment variables
    if environment_vars:
        add_user_defined_variables(environment_vars, hash_tree3, name="Environment Variables")

    # Process items recursively (requests and folders)
    if 'item' in collection:
        process_items(collection['item'], hash_tree3)

    # Convert to XML string with pretty formatting
    xml_str = ET.tostring(jmeter_test_plan, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent="    ")

    # Write to output file
    with open(output_file, 'w') as f:
        f.write(pretty_xml)

def add_user_defined_variables(variables, parent_hash_tree, name="User Defined Variables"):
    """
    Adds User Defined Variables to the JMeter JMX structure.

    Args:
        variables (list): A list of dictionaries, where each dictionary represents a variable
                          with 'key' and 'value' (e.g., from Postman collection or environment).
        parent_hash_tree (ET.Element): The parent hashTree element to which the Arguments element will be added.
        name (str): The name to be displayed for this set of User Defined Variables in JMeter.
    """
    if not variables:
        return

    arguments = ET.SubElement(parent_hash_tree, 'Arguments', {
        'guiclass': 'ArgumentsPanel',
        'testclass': 'Arguments',
        'testname': name,
        'enabled': 'true'
    })
    collection_prop = ET.SubElement(arguments, 'collectionProp', name="Arguments.arguments")

    for var in variables:
        # Ensure 'key' and 'value' exist before processing
        if 'key' in var and 'value' in var:
            element_prop = ET.SubElement(collection_prop, 'elementProp', {
                'name': var['key'],
                'elementType': 'Argument'
            })
            ET.SubElement(element_prop, 'stringProp', name="Argument.name").text = var['key']
            ET.SubElement(element_prop, 'stringProp', name="Argument.value").text = str(var['value'])
            ET.SubElement(element_prop, 'stringProp', name="Argument.metadata").text = '='

    ET.SubElement(parent_hash_tree, 'hashTree') # This hashTree closes the Arguments element

def process_items(items, parent_element):
    """
    Recursively processes Postman collection items (folders and requests).

    Args:
        items (list): A list of Postman collection items.
        parent_element (ET.Element): The parent XML element to which new elements will be added.
    """
    for item in items:
        if 'item' in item:
            # This is a folder, create a JMeter Test Fragment or just process its children directly
            # For simplicity, we'll just process its children directly under the current parent_element
            # without creating a specific folder element in JMX, as JMeter structure is flatter.
            process_items(item['item'], parent_element)
        else:
            # This is a request
            process_request(item, parent_element)

def process_request(item, parent_element):
    """
    Processes a single Postman request and converts it into an HTTPSamplerProxy element.

    Args:
        item (dict): The Postman request item dictionary.
        parent_element (ET.Element): The parent XML element to which the sampler and its hashTree will be added.
    """
    if 'request' not in item:
        return

    request = item['request']

    # Create HTTPSamplerProxy
    sampler = ET.SubElement(parent_element, 'HTTPSamplerProxy', {
        'guiclass': 'HttpTestSampleGui',
        'testclass': 'HTTPSamplerProxy',
        'testname': item.get('name', 'Unnamed Request'),
        'enabled': 'true'
    })

    # Process request body
    if 'body' in request:
        body = request['body']
        if body.get('mode') == 'raw' and 'raw' in body and body['raw']:
            ET.SubElement(sampler, 'boolProp', name="HTTPSampler.postBodyRaw").text = 'true'
            element_prop = ET.SubElement(sampler, 'elementProp', {
                'name': 'HTTPsampler.Arguments',
                'elementType': 'Arguments',
                'guiclass': 'HTTPArgumentsPanel',
                'testclass': 'Arguments',
                'enabled': 'true'
            })
            collection_prop = ET.SubElement(element_prop, 'collectionProp', name="Arguments.arguments")

            arg_element = ET.SubElement(collection_prop, 'elementProp', {
                'name': '', # Name is empty for raw body
                'elementType': 'HTTPArgument'
            })
            ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.always_encode").text = 'false'
            ET.SubElement(arg_element, 'stringProp', name="Argument.value").text = body['raw']
            ET.SubElement(arg_element, 'stringProp', name="Argument.metadata").text = '='
        elif body.get('mode') == 'urlencoded' and 'urlencoded' in body and body['urlencoded']:
            # For x-www-form-urlencoded, JMeter handles parameters as arguments
            element_prop = ET.SubElement(sampler, 'elementProp', {
                'name': 'HTTPsampler.Arguments',
                'elementType': 'Arguments',
                'guiclass': 'HTTPArgumentsPanel',
                'testclass': 'Arguments',
                'enabled': 'true'
            })
            collection_prop = ET.SubElement(element_prop, 'collectionProp', name="Arguments.arguments")

            for param in body['urlencoded']:
                arg_element = ET.SubElement(collection_prop, 'elementProp', {
                    'name': param.get('key', ''),
                    'elementType': 'HTTPArgument'
                })
                ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.always_encode").text = 'false'
                ET.SubElement(arg_element, 'stringProp', name="Argument.value").text = param.get('value', '')
                ET.SubElement(arg_element, 'stringProp', name="Argument.metadata").text = '='
                ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.use_equals").text = 'true'
                ET.SubElement(arg_element, 'stringProp', name="Argument.name").text = param.get('key', '')
        else:
            # Handle other body types or empty body
            element_prop = ET.SubElement(sampler, 'elementProp', {
                'name': 'HTTPsampler.Arguments',
                'elementType': 'Arguments',
                'guiclass': 'HTTPArgumentsPanel',
                'testclass': 'Arguments',
                'enabled': 'true'
            })
            ET.SubElement(element_prop, 'collectionProp', name="Arguments.arguments")
    else:
        # No body in request
        element_prop = ET.SubElement(sampler, 'elementProp', {
            'name': 'HTTPsampler.Arguments',
            'elementType': 'Arguments',
            'guiclass': 'HTTPArgumentsPanel',
            'testclass': 'Arguments',
            'enabled': 'true'
        })
        ET.SubElement(element_prop, 'collectionProp', name="Arguments.arguments")


    # Set common sampler properties
    ET.SubElement(sampler, 'boolProp', name="HTTPSampler.auto_redirects").text = 'false'
    ET.SubElement(sampler, 'boolProp', name="HTTPSampler.follow_redirects").text = 'true'
    ET.SubElement(sampler, 'boolProp', name="HTTPSampler.use_keepalive").text = 'true'
    ET.SubElement(sampler, 'boolProp', name="HTTPSampler.monitor").text = 'false'
    ET.SubElement(sampler, 'boolProp', name="HTTPSampler.DO_MULTIPART_POST").text = 'false' # May need adjustment for multipart/form-data
    ET.SubElement(sampler, 'stringProp', name="HTTPSampler.embedded_url_re")
    ET.SubElement(sampler, 'stringProp', name="HTTPSampler.contentEncoding")

    # Set method
    method = request.get('method', 'GET')
    ET.SubElement(sampler, 'stringProp', name="HTTPSampler.method").text = method

    # Process URL
    if 'url' in request:
        url_data = request['url']
        # Handle cases where url is a string or an object
        if isinstance(url_data, str):
            # Attempt to parse a simple URL string
            from urllib.parse import urlparse
            parsed_url = urlparse(url_data)
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.domain").text = parsed_url.hostname or ''
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.path").text = parsed_url.path or ''
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.protocol").text = parsed_url.scheme or 'http'
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.port").text = str(parsed_url.port) if parsed_url.port else ''
            # Handle query parameters from URL string
            if parsed_url.query:
                # Add query parameters as arguments
                query_args_element_prop = ET.SubElement(sampler, 'elementProp', {
                    'name': 'HTTPsampler.Arguments',
                    'elementType': 'Arguments',
                    'guiclass': 'HTTPArgumentsPanel',
                    'testclass': 'Arguments',
                    'enabled': 'true'
                })
                query_collection_prop = ET.SubElement(query_args_element_prop, 'collectionProp', name="Arguments.arguments")
                from urllib.parse import parse_qs
                query_params = parse_qs(parsed_url.query)
                for key, values in query_params.items():
                    for value in values:
                        arg_element = ET.SubElement(query_collection_prop, 'elementProp', {
                            'name': key,
                            'elementType': 'HTTPArgument'
                        })
                        ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.always_encode").text = 'true'
                        ET.SubElement(arg_element, 'stringProp', name="Argument.value").text = value
                        ET.SubElement(arg_element, 'stringProp', name="Argument.metadata").text = '='
                        ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.use_equals").text = 'true'
                        ET.SubElement(arg_element, 'stringProp', name="Argument.name").text = key

        elif isinstance(url_data, dict):
            # Postman URL object structure
            host = '.'.join(url_data.get('host', ['localhost']))
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.domain").text = host

            # Path can be an array of strings or a single string
            path_parts = url_data.get('path', [])
            if isinstance(path_parts, list):
                path = '/' + '/'.join(path_parts)
            else: # Assume it's a string
                path = path_parts
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.path").text = path

            protocol = url_data.get('protocol', 'http')
            if protocol.endswith(':'): # Remove trailing colon if present
                protocol = protocol[:-1]
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.protocol").text = protocol

            port = url_data.get('port', '')
            ET.SubElement(sampler, 'stringProp', name="HTTPSampler.port").text = str(port) # Ensure port is string

            # Process query parameters if present in URL object
            if 'query' in url_data and url_data['query']:
                # JMeter's HTTP Sampler arguments can include query parameters
                # We need to add them to the same Arguments element as the body, or create a new one
                # For simplicity, let's add them to the main Arguments element if it exists,
                # or create one if not (though the body handling usually creates it).
                # If there's a body, the sampler already has an 'HTTPsampler.Arguments' element.
                # We need to find it and add to its 'collectionProp'.
                # If no body, create a new 'HTTPsampler.Arguments' element.

                # Find or create the Arguments element for query parameters
                args_element = sampler.find("./elementProp[@name='HTTPsampler.Arguments']/collectionProp[@name='Arguments.arguments']")
                if args_element is None:
                    # If no body or existing arguments, create the structure
                    element_prop = ET.SubElement(sampler, 'elementProp', {
                        'name': 'HTTPsampler.Arguments',
                        'elementType': 'Arguments',
                        'guiclass': 'HTTPArgumentsPanel',
                        'testclass': 'Arguments',
                        'enabled': 'true'
                    })
                    args_element = ET.SubElement(element_prop, 'collectionProp', name="Arguments.arguments")

                for param in url_data['query']:
                    if 'key' in param and 'value' in param:
                        arg_element = ET.SubElement(args_element, 'elementProp', {
                            'name': param.get('key', ''),
                            'elementType': 'HTTPArgument'
                        })
                        ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.always_encode").text = 'true' # Query params are usually encoded
                        ET.SubElement(arg_element, 'stringProp', name="Argument.value").text = param.get('value', '')
                        ET.SubElement(arg_element, 'stringProp', name="Argument.metadata").text = '='
                        ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.use_equals").text = 'true'
                        ET.SubElement(arg_element, 'stringProp', name="Argument.name").text = param.get('key', '')


    # Create hashTree for sampler
    sampler_hash_tree = ET.SubElement(parent_element, 'hashTree')

    # Process headers
    if 'header' in request and request['header']:
        header_manager = ET.SubElement(sampler_hash_tree, 'HeaderManager', {
            'guiclass': 'HeaderPanel',
            'testclass': 'HeaderManager',
            'testname': 'HTTP Header Manager',
            'enabled': 'true'
        })
        collection_prop = ET.SubElement(header_manager, 'collectionProp', name="HeaderManager.headers")

        for header in request['header']:
            element_prop = ET.SubElement(collection_prop, 'elementProp', {
                'name': '',
                'elementType': 'Header'
            })
            ET.SubElement(element_prop, 'stringProp', name="Header.name").text = header.get('key', '')
            ET.SubElement(element_prop, 'stringProp', name="Header.value").text = header.get('value', '')

        ET.SubElement(sampler_hash_tree, 'hashTree')

    # Process URL variables (path variables in Postman terminology)
    # These are usually resolved into the path itself, but if they are explicitly
    # defined in Postman's URL object, we can add them as user defined variables
    # specific to this sampler.
    if 'url' in request and isinstance(request['url'], dict) and 'variable' in request['url'] and request['url']['variable']:
        add_user_defined_variables(request['url']['variable'], sampler_hash_tree, name="URL Path Variables")


def main():
    """
    Main function to parse arguments and initiate the conversion.
    """
    parser = argparse.ArgumentParser(description='Convert Postman collection to JMeter JMX')
    parser.add_argument('input', help='Postman collection JSON file')
    parser.add_argument('output', help='Output JMX file')
    parser.add_argument('-e', '--environment', help='Postman environment JSON file (optional)', default=None)
    args = parser.parse_args()

    convert_postman_to_jmx(args.input, args.output, args.environment)
    print(f"Successfully converted {args.input} to {args.output}")

if __name__ == '__main__':
    main()
