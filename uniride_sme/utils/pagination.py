import uniride_sme.utils.exception.exceptions as InvalidInputException


def generate_pagination_metadata(page, page_size, total_count):
    """
    Generate pagination metadata based on the provided parameters.

    Args:
        page (int): The current page.
        page_size (int): The number of items per page.
        total_count (int): The total number of items.

    Returns:
        dict: Metadata for pagination.
    """

    pages = (total_count + page_size - 1) // page_size

    has_next = page < pages
    has_prev = page > 1

    return {
        "page": page,
        "pages": pages,
        "total_count": total_count,
        "prev_page": page - 1 if has_prev else None,
        "next_page": page + 1 if has_next else None,
        "has_next": has_next,
        "has_prev": has_prev,
    }


def create_pagination(request, data):
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("limit", 10))

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    paginated_data = data[start_index:end_index]
    meta = generate_pagination_metadata(page, page_size, len(data))
    return meta, paginated_data
