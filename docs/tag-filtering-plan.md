# Tag Filtering Plan

## Current implementation slice

The first slice adds tag filtering to the existing public review feed. Menu
filtering follows after a menu/catalog model and page exist; this slice does not
invent those product models.

Review filters use repeated `review_tag` query parameters containing tag IDs,
for example `/?review_tag=3&review_tag=7`. The existing tag IDs are used for
this initial slice because tags do not yet have stable slugs.

Filtering semantics are faceted:

- selected tags within one category match with OR;
- selected tags across different categories match with AND;
- unknown tag IDs are ignored;
- no selected tags returns the newest-first unfiltered feed;
- the result set is distinct and retains the existing `-created_at, -id`
  ordering.

## Later menu slice

Before menu filtering, move `TagCategory` and `Tag` from the review-owned app
to a shared catalog/domain app through a data-preserving migration. Menu items
and reviews can then use the same taxonomy. Add stable tag slugs before making
filter URLs part of the long-term public interface.

The shared catalog models and filtering utility are present as groundwork, but
the user-facing menu page and menu route remain deferred until the menu product
requirements are approved.

The future menu filter should reuse the same faceted semantics and accessible
grouped controls, but use a separate query parameter from review filters when
both result sets appear on one page.

## Acceptance criteria

- A review filter can select one or more tags.
- Tags from the same category are alternatives.
- Tags from different categories narrow the result set together.
- Invalid selections do not produce an error or expose unrelated reviews.
- The filter state is represented in the URL and remains visible in the form.
- The unfiltered homepage and review submission behavior remain unchanged.
