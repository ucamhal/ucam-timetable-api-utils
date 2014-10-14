<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- Build indexes marking the existence of modules, series and events in
         the future state. This is an optimisation which allows the 3 
         module/series/event templates below to check for the existence of
         modules/series/events quickly without tree traversal. -->

    <xsl:key name="future-modules"
             match="/states/future/moduleList/module"
             use="concat(path/tripos, '/', path/part, '/', path/subject, '/', name)"/>

    <xsl:key name="future-series"
             match="/states/future/moduleList/module/series"
             use="concat(../path/tripos, '/', ../path/part, '/', ../path/subject, '/', ../name, '/', uniqueid)"/>

    <xsl:key name="future-events"
             match="/states/future/moduleList/module/series/event"
             use="concat(../../path/tripos, '/', ../../path/part, '/', ../../path/subject, '/', ../../name, '/', ../uniqueid, '/', uniqueid)"/>


    <xsl:template match="/states/current/moduleList/module">
        <xsl:choose>
            <!-- If this (currently existing) module does not exist in the
                 future state then mark it for deletion. -->
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
            <!-- If this (currently existing) series does not exist in the
                 future state then mark it for deletion. -->
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
        <!-- If this (currently existing) event does not exist in the
                 future state then mark it for deletion. -->
        <xsl:if test="not(key('future-events', concat(../../path/tripos, '/', ../../path/part, '/', ../../path/subject, '/', ../../name, '/', ../uniqueid, '/', uniqueid)))">
            <xsl:copy>
                <xsl:copy-of select="uniqueid"/>
                <delete/>
            </xsl:copy>
        </xsl:if>
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
