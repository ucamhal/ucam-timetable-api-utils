<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:template match="/moduleList">
		<xsl:copy>
			<xsl:apply-templates select="module">
				<xsl:sort select="path/tripos"/>
				<xsl:sort select="path/part"/>
				<xsl:sort select="path/subject"/>
				<xsl:sort select="name"/>
			</xsl:apply-templates>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="/moduleList/module">
		<xsl:copy>
			<xsl:apply-templates select="*[name()!='series']"/>
			<xsl:apply-templates select="series">
				<xsl:sort select="name"/>
				<xsl:sort select="uniqueid"/>
			</xsl:apply-templates>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="/moduleList/module/series">
		<xsl:copy>
			<xsl:apply-templates select="*[name()!='event']"/>
			<xsl:apply-templates select="event">
				<xsl:sort select="date"/>
				<xsl:sort select="start"/>
				<xsl:sort select="(end|duration)[1]"/>
				<xsl:sort select="name"/>
				<xsl:sort select="type"/>
				<xsl:sort select="location"/>
				<xsl:sort select="lecturer"/>
				<xsl:sort select="uniqueid"/>
			</xsl:apply-templates>
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