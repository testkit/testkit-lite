<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" version="1.0" encoding="UTF-8"
		indent="yes" />
	<xsl:template match="/">
		<html>
			<STYLE type="text/css">
				@import "tests.css";
			</STYLE>

			<body>
				<div id="page">
					<div id="index_page">
						<div id="title">
							<table>
								<tr>
									<td class="title">
										<h1 align="center">Test Report</h1>
									</td>
								</tr>
							</table>
						</div>
						<div id="suite">
							<xsl:for-each select="test_definition/suite">
								<xsl:sort select="@name" />
								<p>
									Test Suite:
									<xsl:value-of select="@name" />
								</p>
								<table>
									<tr>
										<th>Case_ID</th>
										<th>Purpose</th>
										<th>Result</th>
										<th>Stdout</th>
									</tr>
									<xsl:for-each select=".//set">
										<xsl:sort select="@name" />
										<tr>
											<td colspan="4">
												Test Set:
												<xsl:value-of select="@name" />
											</td>
										</tr>
										<xsl:for-each select=".//testcase">
											<xsl:sort select="@id" />
											<tr>
												<td>
													<xsl:value-of select="@id" />
												</td>
												<td>
													<xsl:value-of select="@purpose" />
												</td>

												<xsl:if test="@result = 'FAIL'">
													<td class="red_rate">
														<xsl:value-of select="@result" />
													</td>
												</xsl:if>
												<xsl:if test="@result != 'FAIL'">
													<td class="green_rate">
														<xsl:value-of select="@result" />
													</td>
												</xsl:if>
												<td>
													<xsl:value-of select=".//result_info/stdout" />
													<xsl:if test=".//result_info/stdout = ''">
														N/A
													</xsl:if>
												</td>
											</tr>
										</xsl:for-each>
									</xsl:for-each>
								</table>
							</xsl:for-each>
						</div>
					</div>
				</div>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>