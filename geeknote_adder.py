## geeknote create --notebook "Action Pending" --tags "D01, 1-Now, from_python" --content "from geeknote" --title "Test from geeknote"
import os

def geeknote_add_note(title, notebook="Action Pending", \
                      tags=None, content="from geeknote"):
    cmd = 'geeknote create --title "%s" --notebook "%s" --content "%s"' % \
          (title, notebook, content)
    if tags:
        tag_str = ','.join(tags)
        cmd += ' --tags "%s"' % tag_str
        tags.append('from_python')
        tags.append('geeknote')

    print(cmd)
    os.system(cmd)


def geeknote_add_weekly(title, day, tags, \
                        start_day=None, \
                        end_day=None, \
                        **kwargs):

    geeknote_add_note("Prep Sunday school", notebook="Action Pending", \
                      tags=tags_Thurs, content="from geeknote")
