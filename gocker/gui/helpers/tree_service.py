import logging

from urwidtrees import SimpleTree


def _in_substructure(treelist: list, indent, matcher: callable, updater: callable):
    for index, subtree in enumerate(treelist):
        if matcher(treelist[index][0]):
            if updater is not None:
                treelist[index][0] = updater(subtree[0])
            return True
        logging.debug("%s-%s-%s %s" % ('--' * indent, indent, subtree[0], isinstance(subtree[1], list)))
        if isinstance(subtree[1], list):
            if _in_substructure(subtree[1], indent + 1, matcher, updater):
                return True
    return False


# pylint: disable=protected-access
def update_node(tree: SimpleTree, matcher: callable, updater: callable):
    return _in_substructure(tree._treelist, 0, matcher, updater)


# pylint: disable=protected-access
def find_node(tree: SimpleTree, matcher: callable):
    return _in_substructure(tree._treelist, 0, matcher, None)
