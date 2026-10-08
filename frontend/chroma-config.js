const { ChromaClient } = require('chromadb');
const { DefaultEmbeddingFunction } = require('@chroma-core/default-embed');

const client = new ChromaClient();

const initialize = async () => {
    // Create a collection with embedding function
    const collection = await client.createCollection('restaurant_data', {
        embeddingFunction: new DefaultEmbeddingFunction(),
    });

    // You can add initialization logic here if needed
    console.log('Chroma initialized and collection created.');
};

initialize().catch(console.error);

module.exports = client;