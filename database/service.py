from sqlalchemy.sql import selectable


def joined_table_names(stmt: selectable):
    joined = set()
    for o in stmt.froms:
        if hasattr(o, 'left'):
            joined.add(o.left.fullname)
        if hasattr(o, 'right'):
            joined.add(o.right.fullname)
    return joined
