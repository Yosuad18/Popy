const chroma = require('./chroma-config');

const insertData = async () => {
    const collection = await chroma.createCollection('restaurant_data');

    await collection.add('menu', [
        { item: 'Pizza Margherita', price: 12.99, description: 'Pizza con salsa de tomate, mozzarella y albahaca.' },
        { item: 'Pasta Carbonara', price: 11.99, description: 'Pasta con salsa cremosa, panceta y queso.' },
        { item: 'Ensalada César', price: 9.99, description: 'Ensalada con lechuga, pollo a la parrilla y aderezo César.' }
    ]);

    await collection.add('reservas', [
        { nombre: 'Juan Pérez', fecha: '2023-10-15', hora: '19:00', numeroPersonas: 4 },
        { nombre: 'María Gómez', fecha: '2023-10-16', hora: '20:00', numeroPersonas: 2 }
    ]);

    await collection.add('pedidos', [
        { usuarioId: '1', items: ['Pizza Margherita', 'Ensalada César'], total: 22.98, estado: 'Completo' },
        { usuarioId: '2', items: ['Pasta Carbonara'], total: 11.99, estado: 'En preparación' }
    ]);

    await collection.add('usuarios', [
        { nombre: 'Juan Pérez', email: 'juanperez@example.com', telefono: '555-1234' },
        { nombre: 'María Gómez', email: 'mariagomez@example.com', telefono: '555-5678' }
    ]);

    await collection.add('repartidores', [
        { nombre: 'Carlos López', telefono: '555-9999', estado: 'Disponible' },
        { nombre: 'Laura Martínez', telefono: '555-8888', estado: 'En camino' }
    ]);

    await collection.add('descuentos', [
        { codigo: '10OFF', porcentaje: 10, fechaExpiracion: '2023-12-31' },
        { codigo: 'SAVE5', porcentaje: 5, fechaExpiracion: '2023-11-30' }
    ]);

    console.log('Datos insertados exitosamente.');
};

insertData();