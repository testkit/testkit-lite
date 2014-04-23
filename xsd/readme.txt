= XSLT style for Test Case and Test Result =

== Files structure ==

        readme.txt
        test_definition.xsd   //The schema of test definition
        tests.css             // CSS style for showing test cases and results
        testresult.xsl
        testcase.xsl
        tests.xml             //example of test cases
        result.xml            //example of test result
        
 
 == Applying the style ==
 
 === Update in definition and result XML ===
 
 For applying this style for the definition XML of test cases, please add below statement before the root element of XML (the tag "test_definition").
 
 <?xml-stylesheet type="text/xsl"  href="./testcase.xsl"?>
 
 as below: 
 
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl"  href="./testcase.xsl"?>
<test_definition>

For applying this style for the test-result XML, please add below statement before the root element of XML (the tag "test_definition").
<?xml-stylesheet type="text/xsl"  href="./testresult.xsl"?>

as below:

<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl"  href="./testresult.xsl"?>
<test_definition>

=== Deploy XSLT and CSS style ===

For our test package, below 3 files should be added in each test package. 

        tests.css  
        testresult.xsl
        testcase.xsl
        
For instance, add them under the test package "webapi-tizen-alarm-tests".
 ©¸©¤webapi-tizen-alarm-tests
             ©¸©¤...
             ©¸©¤...
             ©¸tests.css  
             ©¸testresult.xsl
             ©¸testcase.xsl
             ©¸tests.xml
             ©¸...
