import os
import git

def change_state(gh_token):
  repo_url = "github.com/santi-eidu/temp-alert.git"
  repo = git.Repo.clone_from("https://"+repo_url, "./repo-tmp", branch="main")
  repo.git.checkout('--orphan', 'state-branch')
  repo.git.rm('-rf', ".")
  with open('./repo-tmp/state', 'w') as f:
    f.write("0")

  repo.index.add(['state'])
  repo.index.commit("Create storage")
  repo.git.push("https://"+gh_token+"@"+repo_url, "--force")

def main():

  gh_token = os.environ['GITHUB_TOKEN']

  change_state(gh_token)

if __name__ == '__main__':
    main()
