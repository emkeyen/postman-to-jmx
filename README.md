[![Made in Ukraine](https://img.shields.io/badge/made_in-Ukraine-ffd700.svg?labelColor=0057b7)](https://stand-with-ukraine.pp.ua)

# Postman to JMeter Converter

This Python3 script converts your Postman API collections into JMeter test plans. It handles request bodies, headers, URL details and integrates Postman collection and environment variables.

#### Handles:

* **Request bodies:** Raw JSON, x-www-form-urlencoded.
* **Headers:** All your custom headers.
* **URL details:** Host, path, protocol and port.
* **Variables:** Both collection-level vars and env vars from Postman will be added as "User Defined Variables" in JMeter, so you can easily manage dynamic values.

## Running the Script
1. Save the `postman2jmx.py` file
2. Make it executable
```Bash
chmod +x postman2jmx.py
```
3. Export Postman collection and environment (optionally) as a JSON

## Collection Conversion
If you only have a Postman collection and don't use a separate env file:

`./postman2jmx.py <postman_collection.json> <output_jmeter_test_plan.jmx>`


**Example:**
```Bash
./postman2jmx.py collection.json loadsuit.jmx
```

## Collection & Environment Conversion
If you have a Postman environment file that you want to include (recommended for dynamic values like base URLs, tokens, etc.):

```./postman2jmx.py <postman_collection.json> <output_jmeter_test_plan.jmx> -e <postman_environment.json>```

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

* **Pre-request/Test Scripts:** Any JS code you have in Postman's pre-request or test scripts won't be converted. You'll need to re-implement that logic in JMeter using JSR223 samplers or other JMeter elements.

### Contributing

Feel free to open issues or submit pull requests - contributions are always welcome!
