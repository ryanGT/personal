## geeknote create --notebook "Action Pending" --tags "D01, 1-Now, from_python" --content "from geeknote" --title "Test from geeknote"
import os
import date_math

def geeknote_add_note(title, notebook="Action Pending", \
                      tags=None, content="from geeknote"):
    cmd = 'geeknote create --title "%s" --notebook "%s" --content "%s"' % \
          (title, notebook, content)
    
    if tags is None:
        tags = []

    tags.append('from_python')
    tags.append('geeknote')

    tag_str = ','.join(tags)
    cmd += ' --tags "%s"' % tag_str

    print(cmd)
    os.system(cmd)


def geeknote_add_weekly(title, day, tags=None, \
                        start_day=None, \
                        end_day=None, \
                        **kwargs):
    if tags is None:
        tags = []
    day_tags = date_math.get_tags_weekly(day, \
                                         start_day=start_day, \
                                         end_day=end_day)
    tags.extend(day_tags)
    geeknote_add_note(title, notebook="Action Pending", \
                      tags=tags, content="from geeknote")


def geeknote_add_daily(title, tags=None, \
                        start_day=None, \
                        end_day=None, \
                        **kwargs):
    if tags is None:
        tags = []

    day_tags = date_math.get_tags_daily(start_day=start_day, \
                                        end_day=end_day)
    tags.extend(day_tags)
    geeknote_add_note(title, notebook="Action Pending", \
                      tags=tags, content="from geeknote")


def geeknote_add_daily_one_week(title, tags=None, \
                        start_day=None, \
                        **kwargs):
    if tags is None:
        tags = []
    #This method doesnt exist yet:
    day_tags = date_math.get_tags_daily_one_week(start_day=start_day)
    tags.extend(day_tags)
    geeknote_add_note(title, notebook="Action Pending", \
                      tags=tags, content="from geeknote")
