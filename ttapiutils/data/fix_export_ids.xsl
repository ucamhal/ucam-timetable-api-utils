<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:template match="/moduleList/module/series/event/uniqueid[starts-with(., 'import-')]">
		<xsl:copy>
			<!-- Strip off the import- prefix from the text to allow round-tripping the API's exported data. -->
			<xsl:value-of select="substring-after(., 'import-')"/>
		</xsl:copy>
	</xsl:template>

    <xsl:template match="@*|node()">
        <xsl:call-template name="identity"/>
    </xsl:template>

    <xsl:template name="identity">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
