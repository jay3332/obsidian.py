Adding Spotify support to Obsidian.py
=====================================

Obsidian.py has built-in support for Spotify, and it's pretty simple to enable it.

You must have a client ID and secret, which you can generate from Spotify's API dashboard.

**Obsidian.py supports...**

* Spotify albums
* Spotify playlists
* Spotify track URLs
* Spotify search
* Ratelimit handling

Enabling spotify support
------------------------

The recommended way of enabling Spotify support is by passing in two keyword arguments while initiating your node:  
``spotify_client_id`` and ``spotify_client_secret``.

.. code-block:: python

    await obsidian.initiate_node(
        ...,
        spotify_client_id='YOUR_CLIENT_ID',
        spotify_client_secret='YOUR_CLIENT_SECRET'
    )    

If you already have a connected node with a :class:`.SpotifyClient`, you can use this same client in your other node:

.. code-block:: python
    
    await obsidian.initate_node(
        ...
        spotify=other_node.spotify
    )
