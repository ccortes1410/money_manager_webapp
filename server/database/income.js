

module.exports = (sequelize, DataTypes) => {
  const Income = sequelize.define('Income', {
    id: {
        type: DataTypes.INTEGER,
        allowNull: false,
        primaryKey: true,
    },
    user_id: {
        type: DataTypes.INTEGER,
        allowNull: false,
    },
    amount: {
        type: DataTypes.FLOAT,
        allowNull: false,
    },
    source: {
        type: DataTypes.STRING,
        allowNull: false,
    },
    date_received: {
        type: DataTypes.DATE,
        allowNull: false,
    },
    date_intended: {
        type: DataTypes.DATE,
        allowNull: false,
    },
  },
  {
    tableName: "djangoapp_income",
    timestamps: false,
  }
);
    return Income;
};
    