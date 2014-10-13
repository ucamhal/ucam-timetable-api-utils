Timetable API v0 Deletes
========================

This program is a workaround to automatically generate <delete/> operations
required by the Timetable 3 v0 API's XML import feature.

One might assume that submitting an XML file (`<moduleList>`) to
`/api/v0/xmlimport` would result in the API updating the state to match the
given representation. Unfortunately, the submitted XML file is not so much
interpreted as a representation, but as a series of actions to apply. As
such, omitting a module/series/event does not result in it being removed.
Instead, the module/series/event must be explicitly marked for deletion
using a `<delete/>` tag.

This significantly complicates producers of Timetable XML, as they cannot
simply generate a representation of their data in the Timetable format,
they need to know a) what's in Timetable, b) what's in their data set and
c) then work out how to modify a) to get to b).

This program basically performs step c), given a) and b) as inputs.

It pains me that this program needs to exist. The need for it should be
removed at the earliest opportunity.


Usage
-----

FIXME: Automate as much of this as possible. For now some of this is manual.

1. Generate/obtain the new Timetable XML to be imported by `/api/v0/xmlimport`
  1. You might use https://github.com/CUL-DigitalServices/ucam-timetable-engineering-utils for example
2. Using `/api/v0/xmlexport/tripos/$TRIPOS/$PART` (for each part to be imported), obtain the current state of the data in timetable
  1. Run `$ xml tr fix_api_0_export.xsl IA.xml` on each exported XML file to fix the broken exporting of the v0 API, allowing round-tripping.
  2. If you have more than one file, combine them into a single XML file under one `<moduleList>` element.
3. Run `$ python generate_api_v0_deletes.py step2.xml step1.xml > step3.xml`
  1. (Optional) run a command such as `$ xml sel -t -v 'count(//delete)' step3.xml` to ensure you've not screwed something up, resulting in deletes being generated for everything.
4. Import `step3.xml` in `/api/v0/xmlimport`
