const chroma = require('chroma');

const restaurantSchema = {
    menu: [
        { item: String, price: Number, description: String }
    ],
    reservas: [
        { nombre: String, fecha: Date, hora: String, numeroPersonas: Number }
    ],
    pedidos: [
        { usuarioId: String, items: [String], total: Number, estado: String }
    ],
    usuarios: [
        { nombre: String, email: String, telefono: String }
    ],
    repartidores: [
        { nombre: String, telefono: String, estado: String }
    ],
    descuentos: [
        { codigo: String, porcentaje: Number, fechaExpiracion: Date }
    ],
};

chroma.initialize(restaurantSchema);

module.exports = chroma;