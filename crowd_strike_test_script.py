import shutil
import os
import git
import requests
from bs4 import BeautifulSoup


class ValidateUrl(object):
  """It validates url"""
  def __init__(self, url):
    self.url = url
    if self._has_valid_protocol() and self._is_valid_url():
      return  
    raise RuntimeError("Invalid Url!")

  def _has_valid_protocol(self):
    """check if url has http:// or https:// prefix"""
    return isinstance(self.url, str) and (self.url.startswith("http://") or self.url.startswith("https://"))  
  
  def _is_valid_url(self):
    """checks url is valid by sending a get request to the page and returns None or req page object"""
    try:
      self.req_page_obj = requests.get(self.url)
    except requests.exceptions.ConnectionError:
      return False
    else:
      return True
  
  def _read_source(self):
    """read requested page html source to scrape. Should be called after _is_valid_url"""
    return self.req_page_obj.text


class ScrapeWebPage(object):
  _results = list()
  def __init__(self, url):
    self.url = url
    validated_url_obj = ValidateUrl(url)
    self.html = validated_url_obj._read_source()
    self._parse_html(self.html)

  def _parse_html(self, html):
    """Scrape html to get required repo details and create a list of repo details in dict format"""
    self.parser = BeautifulSoup(self.html, 'html.parser')
    all_tr_tags = self.parser.find_all('tr')
    for tr in all_tr_tags:
      all_cells = tr.find_all('td')
      if not all_cells:
        continue
      self._results.append({'name': all_cells[0].get_text(), 'url': all_cells[1].get_text(), 'branch': all_cells[2].get_text()})
  
  def repos(self):
    return self._results


if __name__ == "__main__":
  """Main script"""
  new_file_text = requests.get("http://hck.re/tHEZGP").text
  file_name = "index.js"
  scrapped_web_page = ScrapeWebPage("http://hck.re/crowdstrike")
  repos_list = scrapped_web_page.repos()
  for repo in repos_list:
    if os.path.exists('/tmp/%s' % repo['name']):
      shutil.rmtree('/tmp/%s' % repo['name'])
    repo_obj = git.Repo.clone_from(repo['url'], '/tmp/%s' % repo['name'])
    repo_obj.git.checkout('master', b=repo['branch'])
    new_file_obj = open("%s/%s" % (repo_obj.git.working_dir, file_name), 'a')
    new_file_obj.write(new_file_text)
    new_file_obj.close()
    repo_obj.git.add(file_name)
    repo_obj.git.commit(m="new file added thru code...")
    repo_obj.git.push("origin", "%s" % repo['branch'])

