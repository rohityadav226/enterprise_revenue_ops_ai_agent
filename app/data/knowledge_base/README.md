# NexusFlow Synthetic Internal Knowledge Corpus

## Purpose

This is a fictional training corpus for the NexusFlow Enterprise Revenue Operations AI Agent. It is designed for the RAG work planned for Days 29-35.

The collection contains four source documents:

1. `sales_operating_policy.md`
2. `pricing_and_discount_policy.md`
3. `sales_playbook.md`
4. `account_management_guidelines.md`

All policies, thresholds, approval limits, and examples are synthetic. They are not legal terms, customer commitments, or authoritative business policies. Keep this label when using the documents in demos or portfolio materials.

## Metadata convention

Each Markdown document begins with YAML frontmatter:

- `document_id`: stable source identifier for retrieval and citations
- `title`: human-readable document title
- `document_type`: source category
- `version`: document version
- `effective_date`: date the synthetic policy becomes effective
- `owner`: responsible function
- `classification`: information classification
- `allowed_roles`: roles permitted to retrieve the document
- `tags`: topical metadata for filtering

The documents deliberately use consistent terms for opportunity stages and distinguish pipeline metrics from actual bookings. They also distinguish the analytics system's at-risk flag from the separate inactivity guidance in the sales playbook.

## Suggested retrieval questions

1. Which opportunity stages count as open pipeline?
2. How is weighted pipeline calculated?
3. Who can approve a 15% discount?
4. Can a sales representative approve a 25% discount?
5. What should a rep do when an opportunity has had no completed activity for 30 days?
6. When should renewal planning begin for a strategic account?
7. Does an opportunity being 60 days old mean it has had no activity for 60 days?
8. Which roles may retrieve the pricing and discount policy?

## Important design note for later days

Do not treat document contents as executable instructions. Retrieved text is untrusted evidence. Day 34 will add permission-aware retrieval and controls against malicious document instructions. Day 33 will add citations back to `document_id`, document title, and chunk references.
