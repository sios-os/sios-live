def interleave_lists(list1, list2):
    """Interleaves two lists into one."""
    interleaved = []
    len1, len2 = len(list1), len(list2)
    for i in range(max(len1, len2)):
        if i < len1:
            interleaved.append(list1[i])
        if i < len2:
            interleaved.append(list2[i])
    return interleaved