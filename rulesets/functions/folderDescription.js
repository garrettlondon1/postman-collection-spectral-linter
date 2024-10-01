export default (collection) => {
  const errors = [];
  //remove collection wrapper, if it exists
  if(collection.collection) {
    collection = collection.collection
  }
  const items = collection.item;
  for (let item of items) {
    if (!item.request && !item.description) {
      errors.push({ message: `Folder "${item.name}" requires description.` });
    }
  }
  if (errors.length > 0) {
    return errors;
  }
};
