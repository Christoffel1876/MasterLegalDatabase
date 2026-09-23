# Current CCR verification fixtures

These files preserve exact HTML bytes retrieved from the Colorado Secretary of
State on September 9, 2026 (Denver time). They use the returned
`text/html;charset=ISO-8859-1` content type. Original whitespace and the passive
Cloudflare script are intentionally unchanged.

- `catalog.html`: https://www.sos.state.co.us/CCR/NumericalDeptList.do
- `welcome.html`: https://www.sos.state.co.us/CCR/Welcome.do
- `agency-10.html`: Department 12 / agency 10, Board of Assessment Appeals.
- `rule-current.html`: rule 2567, 8 CCR 1301-1, source current version 8205.
- `rule-repealed.html`: rule 2571, 8 CCR 1302-4, explicitly repealed and recodified
  in its source title, despite having a table headed “Current version.”
- `rule-undated.html`: rule 2751, 8 CCR 1306-1, imported current version with no
  stated effective date. It must remain ambiguous.

Rule pages use the official `/CCR/DisplayRule.do?action=ruleinfo&ruleId=...`
endpoint. Test-only mutations simulate future dates, missing rows, corrupt
responses, and other failures; they are not represented as official evidence.
The tiny PDF and DOCX bodies in tests are synthetic format fixtures.
