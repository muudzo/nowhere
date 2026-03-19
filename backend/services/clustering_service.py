from typing import List


class ClusteringService:
    """Grid-based clustering of geo-coordinates."""

    @staticmethod
    def cluster(
        points: list[tuple[str, float, float]],
        radius_km: float,
    ) -> List[dict]:
        """
        Cluster points by rounding to a grid.
        :param points: list of (member_id, longitude, latitude)
        :param radius_km: search radius — drives grid precision
        :return: list of cluster dicts with centroid + count
        """
        precision = 2 if radius_km > 5 else 3

        clusters: dict[tuple[float, float], dict] = {}

        for _member, r_lon, r_lat in points:
            grid_lat = round(r_lat, precision)
            grid_lon = round(r_lon, precision)
            key = (grid_lat, grid_lon)

            if key not in clusters:
                clusters[key] = {"count": 0, "lat_sum": 0.0, "lon_sum": 0.0}

            clusters[key]["count"] += 1
            clusters[key]["lat_sum"] += r_lat
            clusters[key]["lon_sum"] += r_lon

        results = []
        for key, data in clusters.items():
            count = data["count"]
            results.append({
                "geohash": f"{key[0]},{key[1]}",
                "latitude": data["lat_sum"] / count,
                "longitude": data["lon_sum"] / count,
                "count": count,
            })

        return results
