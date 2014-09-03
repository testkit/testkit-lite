# XSLT style for Test Case and Test Result

## File structure

- readme.txt
- test_definition.xsd   // The schema of test definition
- tests.css             // CSS style for showing test cases and results
- testresult.xsl
- testcase.xsl
- tests.xml             //example of test cases
- result.xml            //example of test result

## Applying the style

### Update in definition and result XML

To apply this style for the definition XML of test cases, please add below statement before the root element of XML (the tag "test_definition").

`<?xml-stylesheet type="text/xsl"  href="./testcase.xsl"?>`

... such as:

```
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl"  href="./testcase.xsl"?>
<test_definition>
```

To apply this style for the test-result XML, please add below statement before the root element of XML (the tag "test_definition").

`<?xml-stylesheet type="text/xsl"  href="./testresult.xsl"?>`

... such as:

```
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl"  href="./testresult.xsl"?>
<test_definition>
```

### Deploy XSLT and CSS style

Please add at least the 3 files into each test package.

- tests.css
- testresult.xsl
- testcase.xsl

... such as:

```
tct-alarm-tizen-tests/
|-- ...
|-- testcase.xsl
|-- testresult.xsl
|-- tests.css
|-- ...
```

