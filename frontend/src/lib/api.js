const API_URL = 'http://yourapiurl.com';

export const fetchMenu = async () => {
    const response = await fetch(`${API_URL}/menu`);
    return response.json();
};

export const fetchReservas = async () => {
    const response = await fetch(`${API_URL}/reservas`);
    return response.json();
};

export const fetchPedidos = async () => {
    const response = await fetch(`${API_URL}/pedidos`);
    return response.json();
};

export const fetchUsuarios = async () => {
    const response = await fetch(`${API_URL}/usuarios`);
    return response.json();
};

export const fetchRepartidores = async () => {
    const response = await fetch(`${API_URL}/repartidores`);
    return response.json();
};

export const fetchDescuentos = async () => {
    const response = await fetch(`${API_URL}/descuentos`);
    return response.json();
};