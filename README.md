# Utah Command Center v6

## What changed
This version adds your OpenAI chat links as default records and refactors the data model to support richer metadata.

## New fields
- itemId
- company
- type
- model
- projectName
- chatName
- details
- url
- importance
- additionalNotes
- dashboard
- category
- tags
- favorite

## Google Sheets workflow
Best options:
1. Maintain your data in Google Sheets
2. Export the sheet to CSV and import the file into the dashboard
3. Or copy rows from the sheet and use **Paste sheet rows**

## Recommended Google Sheets columns
itemId, company, type, model, projectName, chatName, details, url, importance, additionalNotes, dashboard, category, tags, favorite

The paste importer also recognizes your original headers:
- Item ID
- Company
- Type
- Model
- Gem/Project/Agent Name
- Chat Name
- Details
- Link
- Importance
- Additional Notes

## Chrome startup path
file:///C:/Users/Duane/Documents/Dashboards/utah_work_dashboard_v6_sheet_import.html
