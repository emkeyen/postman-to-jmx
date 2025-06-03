# Postman to JMeter Converter

This Python 3 script converts your Postman API collections into JMeter test plans, bridging your API development with load testing. It handles request bodies, headers, URL details and integrates Postman collection and env vars.

## What it Does
* **Request bodies:** Raw JSON, x-www-form-urlencoded.
* **Headers:** All your custom headers.
* **URL details:** Host, path, protocol and port.
* **Variables:** Both collection-level vars and env vars from Postman will be added as "User Defined Variables" in JMeter, so you can easily manage dynamic values.

## Running the Script
1. **Save the script:** Save the Python code you have as `postman2jmx.py`.
2. **Make it executable:** Open your terminal and run:
```Bash
chmod +x postman2jmx.py
```
3. **Get your Postman files:** Export your Postman Collection as a JSON file. 
If you use environment variables, export your Postman Environment as a JSON file too.

Now, open your terminal or command prompt and navigate to where you saved the script.

## Basic Conversion (Collection Only)
If you only have a Postman Collection and don't use a separate environment file:

`./postman2jmx.py <your_postman_collection.json> <output_jmeter_test_plan.jmx>`


**Example:**
```Bash
./postman2jmx.py collection.json loadsuit.jmx
```

## With a Postman Environment
If you have a Postman env file that you want to include (highly recommended for dynamic values like base URLs, tokens, etc.):

```./postman2jmx.py <your_postman_collection.json> <output_jmeter_test_plan.jmx> -e <your_postman_environment.json>```

**Example:**
```Bash
./postman2jmx.py collection.json loadsuit.jmx -e env.json
```

### After Conversion
Once the script runs, you'll find your new .jmx file in the specified output location. You can then open this .jmx file directly in JMeter and start configuring your performance tests :)

### Notes

* **Variables:** Variables from your Postman Collection and Environment will appear as "User Defined Variables" in JMeter. Remember that in JMeter, you reference these variables using ${variable_name}.

* **Folders:** Postman folders are currently flattened into the main Thread Group in JMeter.

* **Body types:** The script handles raw JSON and x-www-form-urlencoded bodies. Other complex body types (like formdata with file uploads) might need manual adjustment in JMeter after conversion.

* **Pre-request/Test Scripts:** Any JavaScript code you have in Postman's pre-request or test scripts won't be converted. You'll need to re-implement that logic in JMeter using JSR223 Samplers or other JMeter elements.