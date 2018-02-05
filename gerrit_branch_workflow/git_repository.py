import itertools

import git


class GitRemoteProgressStdout(git.remote.RemoteProgress):

    def line_dropped(self, line):
        super().line_dropped(line)
        print(line)


class GitRepository(object):

    def __init__(self, repository_path):
        self.repo = git.Repo(repository_path)

    def current_branch_name(self):
        return self.repo.active_branch.name

    def untracked_files(self):
        return self.repo.untracked_files

    def is_dirty(self):
        return self.repo.is_dirty()

    def create_local_branch(self, branch):
        self._validate_local_branch_does_not_exist(branch)
        self.repo.create_head(branch)

    def create_remote_tracking_branch(self, branch):
        self._validate_local_branch_exists(branch)
        origin = self.repo.remotes['origin']
        origin.push(
            '{}:{}'.format(branch, branch), progress=GitRemoteProgressStdout())
        self.repo.heads[branch].set_tracking_branch(origin.refs[branch])

    def checkout_branch(self, branch):
        self._validate_local_branch_exists(branch)
        self.repo.heads[branch].checkout()

    def delete_local_branch(self, branch, force=False):
        self._validate_local_branch_exists(branch)
        self.repo.delete_head(branch, force=force)

    def delete_remote_tracking_branch(self, branch):
        self._validate_remote_branch_exists(branch)
        self.repo.remotes['origin'].push(
            ':{}'.format(branch), progress=GitRemoteProgressStdout())

    def merge_base(self, ancestor_branch):
        self._validate_local_branch_exists(ancestor_branch)
        return self.repo.merge_base(ancestor_branch, self.current_branch_name())

    def soft_reset_to_commit(self, commit):
        self.repo.head.reset(commit, index=False)

    def get_branch_commits(self, ancestor_branch):
        self._validate_local_branch_exists(ancestor_branch)
        last_ancestor_commit = self.merge_base(ancestor_branch)
        if len(last_ancestor_commit) != 1:
            raise ValueError(
                'ancestor branch "{}" has been merged and forked multiple '
                'times, unsupported branch structure.'.format(ancestor_branch))

        current_branch = self.repo.active_branch.name
        return [
            commit
            for commit in itertools.takewhile(
                lambda x: x != last_ancestor_commit[0],
                self.repo.iter_commits(current_branch))
        ]

    def commit(self, message):
        return self.repo.index.commit(message)

    def push_to_non_tracking_branch(self, local_branch, remote_ref):
        self._validate_local_branch_exists(local_branch)
        origin = self.repo.remotes['origin']
        origin.push(
            '{}:{}'.format(local_branch, remote_ref),
            progress=GitRemoteProgressStdout())

    def _validate_local_branch_exists(self, branch):
        if branch not in self.repo.heads:
            raise ValueError('local branch "{}" does not exist.'.format(branch))

    def _validate_local_branch_does_not_exist(self, branch):
        if branch in self.repo.heads:
            raise ValueError('local branch "{}" already exists.'.format(branch))

    def _validate_remote_branch_exists(self, branch):
        if branch not in self.repo.remotes['origin'].refs:
            raise ValueError(
                'remote branch "{}" does not exist.'.format(branch))
