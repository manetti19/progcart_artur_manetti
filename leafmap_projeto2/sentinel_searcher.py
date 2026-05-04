# Importa o Client, que permite acessar catálogos STAC.
from pystac_client import Client

# Importa o planetary_computer, usado para assinar os links das imagens.
import planetary_computer


# Cria uma classe responsável por buscar imagens Sentinel-2.
class SentinelSearcher:

    # Método inicial da classe.
    def __init__(self):

        # Define a URL do catálogo STAC do Microsoft Planetary Computer.
        self.catalog_url = "https://planetarycomputer.microsoft.com/api/stac/v1"

        # Define a coleção de imagens Sentinel-2 Level-2A.
        self.collection = "sentinel-2-l2a"

        # Define o intervalo de datas para buscar imagens.
        self.datetime_interval = "2024-01-01/2026-04-29"

        # Define o limite máximo de cobertura de nuvens.
        self.max_cloud_cover = 20

        # Define o tamanho da área ao redor da coordenada central.
        self.delta = 0.05

        # Abre o catálogo STAC.
        self.catalog = Client.open(self.catalog_url)


    # Método responsável por criar o bbox a partir de latitude e longitude.
    def criar_bbox(self, latitude, longitude):

        # Calcula o limite oeste do bbox.
        min_lon = longitude - self.delta

        # Calcula o limite sul do bbox.
        min_lat = latitude - self.delta

        # Calcula o limite leste do bbox.
        max_lon = longitude + self.delta

        # Calcula o limite norte do bbox.
        max_lat = latitude + self.delta

        # Cria o bbox no formato usado pelo STAC.
        bbox = [min_lon, min_lat, max_lon, max_lat]

        # Retorna o bbox criado.
        return bbox


    # Método responsável por buscar uma imagem Sentinel-2.
    def buscar_imagem(self, latitude, longitude):

        # Cria o bbox usando as coordenadas recebidas.
        bbox = self.criar_bbox(latitude, longitude)

        # Faz a busca no catálogo STAC.
        search = self.catalog.search(
            collections=[self.collection],
            bbox=bbox,
            datetime=self.datetime_interval,
            query={
                "eo:cloud_cover": {
                    "lt": self.max_cloud_cover
                }
            },
            max_items=10
        )

        # Converte os resultados encontrados em uma lista.
        items = list(search.items())

        # Verifica se nenhuma imagem foi encontrada.
        if len(items) == 0:

            # Retorna None caso não encontre imagem.
            return None

        # Ordena as imagens pela menor cobertura de nuvens.
        items.sort(
            key=lambda item: item.properties.get("eo:cloud_cover", 999)
        )

        # Seleciona a melhor imagem encontrada.
        item = items[0]

        # Assina o item para liberar o acesso aos links dos assets.
        signed_item = planetary_computer.sign(item)

        # Verifica se existe um preview renderizado.
        if "rendered_preview" in signed_item.assets:

            # Pega o link do preview renderizado.
            image_url = signed_item.assets["rendered_preview"].href

        # Caso não exista preview renderizado, tenta usar o asset visual.
        elif "visual" in signed_item.assets:

            # Pega o link da imagem visual.
            image_url = signed_item.assets["visual"].href

        # Caso não exista nenhum asset visual disponível.
        else:

            # Retorna None caso não exista imagem visual.
            return None

        # Cria um dicionário com as informações da imagem encontrada.
        resultado = {
            "bbox": bbox,
            "image_url": image_url,
            "data": item.properties.get("datetime"),
            "cobertura_nuvens": item.properties.get("eo:cloud_cover"),
            "id": item.id
        }

        # Retorna o resultado da busca.
        return resultado