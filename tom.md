{% for post in posts %}
  		{% if current_user.has_liked_post(post) %}
    	<a href="{{ url_for('action_like', post_id=post.id, action='unlike') }}">Unlike</a>
  	{% else %}
    	<a href="{{ url_for('action_like', post_id=post.id, action='like') }}">Like</a>
  		{% endif %}
  		{{ post.likes.count() }} likes
	{% endfor %}



<div class="dislike" id=dislike"

{% for post in posts %}

{% endfor %}


{{ post.likes.count() }} likes

<a href="{{ url_for('action_like', post_id=post.id, action='unlike') }}">Unlike</a>
  	{% else %}
    	<a href="{{ url_for('action_like', post_id=post.id, action='like') }}">Like</a>