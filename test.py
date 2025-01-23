from spotapi import Public

# Exemple d'ID ou URI d'un artiste (par exemple, ID de Spotify : "1Xyo4u8uXC1ZmMpatF05PJ")
artist_id = "1Xyo4u8uXC1ZmMpatF05PJ"  # ID ou URI de l'artiste
artist_info = Public.artist(artist_id)

# Affichage des informations de l'artiste
print(f"Nom : {artist_info['name']}")
print(f"Popularité : {artist_info['popularity']}")
print(f"Genres : {artist_info['genres']}")