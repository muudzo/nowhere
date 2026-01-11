import * as Location from 'expo-location';

export interface CoarseLocation {
    latitude: number;
    longitude: number;
}

export async function getCurrentLocation(): Promise<CoarseLocation | null> {
    let { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
        return null;
    }

    // Use low accuracy for "coarse" and speed
    let location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
    });

    // Rounding for privacy logic in frontend too?
    // Backend enforces it, but let's be consistent.
    // 3 decimal places is ~110m
    const lat = parseFloat(location.coords.latitude.toFixed(3));
    const lon = parseFloat(location.coords.longitude.toFixed(3));

    return { latitude: lat, longitude: lon };
}
