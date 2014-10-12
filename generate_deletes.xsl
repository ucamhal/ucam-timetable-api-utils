<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- hit each module/series/event by applying templates
         when we hit each one:
            - insert it from the new state if it's in just the new state or in both
            - insert a delete element if it's in just the old
        -->

    <!-- TODO: remove the name from the use expression and change name to future-modules.
               Because we never query for existing ones -->
    <xsl:key name="future-modules"
             match="/states/future/moduleList/module"
             use="concat(path/tripos, '/', path/part, '/', path/subject, '/', name)"/>

    <xsl:key name="future-series"
             match="/states/future/moduleList/module/series"
             use="concat(../path/tripos, '/', ../path/part, '/', ../path/subject, '/', ../name, '/', uniqueid)"/>

    <xsl:key name="future-events"
             match="/states/future/moduleList/module/series/event"
             use="concat(../../path/tripos, '/', ../../path/part, '/', ../../path/subject, '/', ../../name, '/', ../uniqueid, '/', uniqueid)"/>

    <!-- modules-by-part
         series-by-part -->

    <!-- <xsl:template match="/states">
        <xsl:message>
            <xsl:text>STARTING</xsl:text>
        </xsl:message>
        <moduleList>
            <xsl:apply-templates select="current/moduleList/module|future/moduleList/module"/>
        </moduleList>
    </xsl:template> -->

    <xsl:template match="/states/current/moduleList/module">
        <xsl:choose>
            <xsl:when test="not(key('future-modules', concat(path/tripos, '/', path/part, '/', path/subject, '/', name)))">
                <xsl:copy>
                    <xsl:copy-of select="path"/>
                    <delete/>
                </xsl:copy>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="identity"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="/states/current/moduleList/module/series">
        <xsl:choose>
            <xsl:when test="not(key('future-series', concat(../path/tripos, '/', ../path/part, '/', ../path/subject, '/', ../name, '/', uniqueid)))">
                <xsl:copy>
                    <xsl:copy-of select="uniqueid"/>
                    <xsl:copy-of select="name"/>
                    <delete/>
                </xsl:copy>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="identity"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="/states/current/moduleList/module/series/event">
        <xsl:choose>
            <xsl:when test="not(key('future-events', concat(../../path/tripos, '/', ../../path/part, '/', ../../path/subject, '/', ../../name, '/', ../uniqueid, '/', uniqueid)))">
                <xsl:copy>
                    <xsl:copy-of select="uniqueid"/>
                    <delete/>
                </xsl:copy>
            </xsl:when>
            <xsl:otherwise>
                <!-- <xsl:call-template name="identity"/> -->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- <xsl:template match="module[name(../../)='future']">
        <xsl:call-template name="identity"/>
    </xsl:template> -->

    <xsl:template match="@*|node()">
        <xsl:call-template name="identity"/>
    </xsl:template>

    <xsl:template name="identity">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
