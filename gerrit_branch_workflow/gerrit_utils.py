import re


def commit_message_without_change_id(commit_msg):
    return re.sub(r'Change-Id:.*?\n', '', commit_msg)


def change_id_without_commit_message(commit_msg):
    found = re.search(r'.*?Change-Id: (.*?)\n', commit_msg)
    if not found or len(found.groups()) != 1:
        raise ValueError('no change id present in "{}"'.format(commit_msg))

    return found.group(1)


def flattened_commit_message_from_commits(commits):
    msg = ''
    for commit in commits:
        msg += commit_message_without_change_id(commit.message)
        msg += '=== commit {} by {} <{}> ===\n\n'.format(
            str(commit.authored_datetime), commit.committer.name,
            commit.committer.email)
    msg += '\nChange-Id: {}\n'.format(
        change_id_without_commit_message(commits[-1].message))
    return msg


def push_branch_for_review(repo, staging_branch_name):
    repo.push_to_non_tracking_branch(staging_branch_name, 'refs/for/master')
