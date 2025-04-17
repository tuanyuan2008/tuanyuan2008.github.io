---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: page
title: Blog
---

Welcome to my blog! Here you can find my thoughts and experiences on various topics.

## Explore Posts

- [View All Posts](/blog/archive)
- [Blog Clusters](/blog/clustering) - Explore similar posts through ML-powered clustering

## Recent Posts

{% for post in site.posts limit:5 %}
- [{{ post.title }}]({{ post.url }})
{% endfor %}
